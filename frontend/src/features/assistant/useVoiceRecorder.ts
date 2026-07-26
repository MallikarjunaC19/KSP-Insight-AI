import { useState, useRef, useCallback } from 'react'

export function useVoiceRecorder() {
  const [isRecording, setIsRecording] = useState(false)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])

  const startRecording = useCallback(async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    const recorder = new MediaRecorder(stream)
    chunksRef.current = []

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data)
    }

    recorder.start()
    mediaRecorderRef.current = recorder
    setIsRecording(true)
  }, [])

  const stopRecording = useCallback((): Promise<Blob> => {
    return new Promise((resolve) => {
      const recorder = mediaRecorderRef.current
      if (!recorder) return
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        recorder.stream.getTracks().forEach((track) => track.stop())
        setIsRecording(false)
        resolve(blob)
      }
      recorder.stop()
    })
  }, [])

  return { isRecording, startRecording, stopRecording }
}