"use client"

import { useState, useCallback } from "react"
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

  // NEW: Upload file
  const uploadFile = useCallback(async (file: File): Promise<string> => {
    try {
      setError(null)
      setUploadProgress({ fileName: file.name, status: "uploading" })
      
      const result = await chatAPI.uploadFile(file)
      
      setUploadProgress({ fileName: file.name, status: "success" })
      
      // Clear upload status after 3 seconds
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

  // NEW: Streaming send message
  const sendMessageStream = useCallback(
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
          if (chunk.type === "content" && chunk.content) {
            setMessages((prev) => {
              const updated = [...prev]
              const lastMsg = updated[updated.length - 1]
              
              if (lastMsg && lastMsg.sender === "ai") {
                // Check if content contains tool results (JSON-like patterns)
                const toolResultPattern = /\{'path':.*?\}/g
                const content = chunk.content
                
                if (toolResultPattern.test(content)) {
                  // Create separate tool message
                  const toolContent = content.match(toolResultPattern)?.[0] || content
                  updated.push({
                    sender: "tool",
                    content: toolContent,
                    timestamp: Date.now()
                  })
                  // Continue AI message after tool
                  updated.push({
                    sender: "ai",
                    content: "",
                    timestamp: Date.now()
                  })
                } else {
                  // Normal AI content accumulation
                  updated[updated.length - 1] = {
                    ...lastMsg,
                    content: lastMsg.content + content
                  }
                }
              }
              return updated
            })
          } else if (chunk.type === "done") {
            setIsLoading(false)
          } else if (chunk.type === "error") {
            setError(chunk.error || "Stream error occurred")
            setIsLoading(false)
          }
        })

      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Failed to send message"
        setError(errorMessage)
        console.error(errorMessage)
        
        // Remove failed messages
        setMessages((prev) => prev.slice(0, -2))
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    [currentSessionId]
  )

  // Legacy non-streaming method
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