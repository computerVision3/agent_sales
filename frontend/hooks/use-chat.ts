"use client"

import { useState, useCallback, useRef } from "react"
import { chatAPI, type ChatMessage, type StreamChunk } from "@/lib/api"

function stringifyContent(content: any): string {
  if (typeof content === "string") return content
  if (typeof content === "object" && content !== null) return JSON.stringify(content, null, 2)
  return String(content ?? "")
}

export function useChat() {
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [uploadProgress, setUploadProgress] = useState<{fileName: string, status: "uploading" | "success" | "error"} | null>(null)
  
  // Track active stream to abort on session change
  const activeStreamRef = useRef<{ sessionId: string; aborted: boolean } | null>(null)

  const createNewSession = useCallback(async () => {
    try {
      setError(null)
      setIsLoading(true)
      const response = await chatAPI.createNewChat()
      setCurrentSessionId(response.session_id)
      setMessages([])
      return response.session_id
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to create new session"
      setError(errorMessage)
      console.error(errorMessage)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  const loadSession = useCallback(async (sessionId: string) => {
    try {
      // Abort any active stream
      if (activeStreamRef.current) {
        activeStreamRef.current.aborted = true
        activeStreamRef.current = null
      }

      setError(null)
      setIsLoading(true)
      const response = await chatAPI.getMessagesBySession(sessionId)
      setCurrentSessionId(sessionId)
      
      const mappedMessages: ChatMessage[] = response.message.map((item: any) => ({
        sender: item.sender || "ai",
        content: stringifyContent(item.content),
        timestamp: Date.now(),
      }))
      
      setMessages(mappedMessages)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to load session"
      setError(errorMessage)
      console.error(errorMessage)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  const uploadFile = useCallback(async (file: File): Promise<string> => {
    try {
      setError(null)
      setUploadProgress({ fileName: file.name, status: "uploading" })
      
      const result = await chatAPI.uploadFile(file)
      
      setUploadProgress({ fileName: file.name, status: "success" })
      setTimeout(() => setUploadProgress(null), 3000)
      
      return result
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to upload file"
      setError(errorMessage)
      setUploadProgress({ fileName: file.name, status: "error" })
      setTimeout(() => setUploadProgress(null), 3000)
      throw err
    }
  }, [])

  const sendMessageStream = useCallback(
    async (userInput: string, sessionId?: string) => {
      const targetSessionId = sessionId || currentSessionId
      
      if (!targetSessionId) {
        throw new Error("No active session")
      }

      // Abort previous stream if exists
      if (activeStreamRef.current) {
        activeStreamRef.current.aborted = true
      }

      // Create new stream tracker
      const streamTracker = { sessionId: targetSessionId, aborted: false }
      activeStreamRef.current = streamTracker

      try {
        setError(null)
        setIsLoading(true)

        if (sessionId && sessionId !== currentSessionId) {
          setCurrentSessionId(sessionId)
        }

        // Add user message
        const userMessage: ChatMessage = {
          sender: "human",
          content: userInput,
          timestamp: Date.now(),
        }
        setMessages((prev) => [...prev, userMessage])

        // Add placeholder for AI message
        const aiMessage: ChatMessage = {
          sender: "ai",
          content: "",
          timestamp: Date.now(),
        }
        setMessages((prev) => [...prev, aiMessage])

        // Stream response
        await chatAPI.sendMessageStream(targetSessionId, userInput, (chunk: StreamChunk) => {
          // Check if this stream was aborted (session changed)
          if (streamTracker.aborted) {
            console.log("[useChat] Stream aborted - session changed")
            return
          }

          if (chunk.type === "content" && chunk.content) {
            setMessages((prev) => {
              const updated = [...prev]
              const lastMsg = updated[updated.length - 1]
              
              if (lastMsg && lastMsg.sender === "ai") {
                const toolResultPattern = /\{'path':.*?\}/g
                const content = chunk.content
                
                if (toolResultPattern.test(content)) {
                  const toolContent = content.match(toolResultPattern)?.[0] || content
                  updated.push({
                    sender: "tool",
                    content: toolContent,
                    timestamp: Date.now()
                  })
                  updated.push({
                    sender: "ai",
                    content: "",
                    timestamp: Date.now()
                  })
                } else {
                  updated[updated.length - 1] = {
                    ...lastMsg,
                    content: lastMsg.content + content
                  }
                }
              }
              return updated
            })
          } else if (chunk.type === "done") {
            // Only clear loading if stream wasn't aborted
            if (!streamTracker.aborted) {
              setIsLoading(false)
              // Clear active stream reference
              if (activeStreamRef.current === streamTracker) {
                activeStreamRef.current = null
              }
            }
          } else if (chunk.type === "error") {
            if (!streamTracker.aborted) {
              setError(chunk.error || "Stream error occurred")
              setIsLoading(false)
            }
          }
        })

      } catch (err) {
        // Only handle error if stream wasn't aborted
        if (!streamTracker.aborted) {
          const errorMessage = err instanceof Error ? err.message : "Failed to send message"
          setError(errorMessage)
          console.error(errorMessage)
          
          // Remove failed messages
          setMessages((prev) => prev.slice(0, -2))
        }
        throw err
      } finally {
        // Only clear loading if stream wasn't aborted
        if (!streamTracker.aborted) {
          setIsLoading(false)
        }
      }
    },
    [currentSessionId]
  )

  const sendMessage = useCallback(
    async (userInput: string, sessionId?: string) => {
      const targetSessionId = sessionId || currentSessionId
      
      if (!targetSessionId) {
        throw new Error("No active session")
      }

      try {
        setError(null)
        setIsLoading(true)

        if (sessionId && sessionId !== currentSessionId) {
          setCurrentSessionId(sessionId)
        }

        const userMessage: ChatMessage = {
          sender: "human",
          content: userInput,
          timestamp: Date.now(),
        }

        setMessages((prev) => [...prev, userMessage])

        const response = await chatAPI.sendMessage(targetSessionId, userInput)

        const aiMessages: ChatMessage[] = Array.isArray(response.conversation)
          ? response.conversation
              .slice(1)
              .map((content: any) => ({
                sender: "ai",
                content: String(content),
                timestamp: Date.now(),
              }))
          : []

        setMessages((prev) => [...prev, ...aiMessages])
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Failed to send message"
        setError(errorMessage)
        console.error(errorMessage)
        
        setMessages((prev) => prev.slice(0, -1))
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    [currentSessionId]
  )

  const sendMessageWithAutoSession = useCallback(
    async (userInput: string, useStreaming: boolean = true) => {
      try {
        if (!currentSessionId) {
          const newSessionId = await createNewSession()
          if (newSessionId) {
            if (useStreaming) {
              await sendMessageStream(userInput, newSessionId)
            } else {
              await sendMessage(userInput, newSessionId)
            }
          }
        } else {
          if (useStreaming) {
            await sendMessageStream(userInput)
          } else {
            await sendMessage(userInput)
          }
        }
      } catch (err) {
        console.error("Failed to send message with auto session:", err)
        throw err
      }
    },
    [currentSessionId, createNewSession, sendMessage, sendMessageStream]
  )

  const clearSession = useCallback(() => {
    // Abort any active stream
    if (activeStreamRef.current) {
      activeStreamRef.current.aborted = true
      activeStreamRef.current = null
    }
    
    setCurrentSessionId(null)
    setMessages([])
    setError(null)
    setUploadProgress(null)
  }, [])

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  return {
    currentSessionId,
    messages,
    isLoading,
    error,
    uploadProgress,
    createNewSession,
    loadSession,
    sendMessage,
    sendMessageStream,
    sendMessageWithAutoSession,
    uploadFile,
    clearSession,
    clearError,
  }
}