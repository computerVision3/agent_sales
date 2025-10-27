"use client"

import { useState, useRef, type KeyboardEvent } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Send, Paperclip, X } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"

interface MessageInputProps {
  onSendMessage: (message: string) => void
  onFileUpload?: (file: File) => Promise<void>
  disabled?: boolean
  placeholder?: string
  uploadProgress?: {fileName: string, status: "uploading" | "success" | "error"} | null
}

export function MessageInput({
  onSendMessage,
  onFileUpload,
  disabled = false,
  placeholder = "Type your message...",
  uploadProgress,
}: MessageInputProps) {
  const [message, setMessage] = useState("")
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleSend = async () => {
    if (!message.trim() && !selectedFile) return
    if (disabled) return

    // Upload file first if selected
    if (selectedFile && onFileUpload) {
      try {
        await onFileUpload(selectedFile)
        setSelectedFile(null)
      } catch (err) {
        console.error("File upload failed:", err)
        return
      }
    }

    // Send message
    if (message.trim()) {
      onSendMessage(message.trim())
      setMessage("")
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
    }
  }

  const removeFile = () => {
    setSelectedFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
  }

  return (
    <div className="border-t bg-white p-4">
      {/* Upload Progress */}
      <AnimatePresence>
        {uploadProgress && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mb-3"
          >
            <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm ${
              uploadProgress.status === "uploading" ? "bg-blue-50 text-blue-700" :
              uploadProgress.status === "success" ? "bg-green-50 text-green-700" :
              "bg-red-50 text-red-700"
            }`}>
              {uploadProgress.status === "uploading" && (
                <div className="w-4 h-4 border-2 border-blue-700 border-t-transparent rounded-full animate-spin"></div>
              )}
              {uploadProgress.status === "success" && (
                <div className="w-4 h-4 bg-green-700 rounded-full flex items-center justify-center text-white text-xs">✓</div>
              )}
              {uploadProgress.status === "error" && (
                <div className="w-4 h-4 bg-red-700 rounded-full flex items-center justify-center text-white text-xs">✕</div>
              )}
              <span className="font-medium">{uploadProgress.fileName}</span>
              <span className="text-xs">
                {uploadProgress.status === "uploading" && "Uploading..."}
                {uploadProgress.status === "success" && "Uploaded successfully"}
                {uploadProgress.status === "error" && "Upload failed"}
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Selected File Preview */}
      <AnimatePresence>
        {selectedFile && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mb-3"
          >
            <div className="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg">
              <Paperclip className="w-4 h-4 text-gray-600" />
              <span className="text-sm text-gray-700 flex-1 truncate">{selectedFile.name}</span>
              <span className="text-xs text-gray-500">{(selectedFile.size / 1024).toFixed(1)} KB</span>
              <button
                onClick={removeFile}
                className="p-1 hover:bg-gray-200 rounded transition-colors"
              >
                <X className="w-4 h-4 text-gray-600" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex gap-3 items-end">
        {/* File Upload Button */}
        <div>
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileSelect}
            className="hidden"
            disabled={disabled}
          />
          <Button
            type="button"
            variant="outline"
            size="lg"
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled}
            className="px-4 py-3"
          >
            <Paperclip className="w-4 h-4" />
          </Button>
        </div>

        {/* Message Input */}
        <Textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          className="flex-1 min-h-[60px] max-h-[120px] resize-none"
          rows={2}
        />

        {/* Send Button */}
        <Button 
          onClick={handleSend} 
          disabled={disabled || (!message.trim() && !selectedFile)} 
          size="lg" 
          className="px-4 py-3"
        >
          <Send className="w-4 h-4" />
        </Button>
      </div>
      
      <div className="text-xs text-gray-500 mt-2">
        Press Enter to send, Shift+Enter for new line {onFileUpload && "• Click 📎 to attach files"}
      </div>
    </div>
  )
}