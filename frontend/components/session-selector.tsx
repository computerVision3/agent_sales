"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Trash2, RefreshCw, MessageCircle } from "lucide-react"
import { chatAPI } from "@/lib/api"
import { motion, AnimatePresence } from "framer-motion"

interface SessionSelectorProps {
  currentSessionId: string | null
  onSessionChange: (sessionId: string | null) => void
  onNewSession: () => void
}

export function SessionSelector({ currentSessionId, onSessionChange }: SessionSelectorProps) {
  const [sessions, setSessions] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isDeleting, setIsDeleting] = useState<string | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [sessionToDelete, setSessionToDelete] = useState<string | null>(null)

  const loadSessions = async () => {
    try {
      setIsLoading(true)
      const response = await chatAPI.getAllSessions()
      setSessions(response.session_ids)
    } catch (error) {
      console.error("Failed to load sessions:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeleteClick = (sessionId: string, e?: React.MouseEvent) => {
    if (e) {
      e.preventDefault()
      e.stopPropagation()
    }
    setSessionToDelete(sessionId)
    setDeleteDialogOpen(true)
  }

  const handleConfirmDelete = async () => {
    if (!sessionToDelete) return
    try {
      setIsDeleting(sessionToDelete)
      await chatAPI.deleteSession(sessionToDelete)
      setSessions((prev) => prev.filter((id) => id !== sessionToDelete))
      if (sessionToDelete === currentSessionId) {
        onSessionChange(null)
      }
    } catch (error) {
      console.error("Failed to delete session:", error)
    } finally {
      setIsDeleting(null)
      setDeleteDialogOpen(false)
      setSessionToDelete(null)
    }
  }

  const formatSessionId = (sessionId: string) => {
    const parts = sessionId.split("_")
    if (parts.length >= 3) {
      const timestamp = Number.parseInt(parts[1])
      const date = new Date(timestamp)
      return `Chat ${date.toLocaleDateString()} ${date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`
    }
    return `${sessionId.slice(0, 12)}...`
  }

  useEffect(() => {
    loadSessions()
  }, [])

  return (
    <>
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-gray-700">Chat Sessions</h3>
          <Button
            variant="ghost"
            size="sm"
            onClick={loadSessions}
            disabled={isLoading}
            className="h-6 w-6 p-0"
          >
            <RefreshCw className={`w-3 h-3 ${isLoading ? 'animate-spin' : ''}`} />
          </Button>
        </div>

        {/* Dropdown */}
        <div className="space-y-2">
          <label className="text-xs text-gray-600">Switch Session</label>
          <Select
            value={currentSessionId || ""}
            onValueChange={(value) => onSessionChange(value || null)}
            disabled={isLoading || sessions.length === 0}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select chat session" />
            </SelectTrigger>
            <SelectContent className="w-full">
              {sessions.map((sessionId) => (
                <div key={sessionId} className="relative group">
                  <SelectItem value={sessionId} className="pr-10">
                    <div className="flex items-center gap-2 w-full">
                      <MessageCircle className="w-3 h-3 text-gray-500 flex-shrink-0" />
                      <span className="flex-1 truncate">{formatSessionId(sessionId)}</span>
                      {sessionId === currentSessionId && (
                        <span className="text-xs text-blue-600 font-medium">(Active)</span>
                      )}
                    </div>
                  </SelectItem>

                  {/* Inline Delete Button */}
                  <button
                    onClick={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      handleDeleteClick(sessionId)
                    }}
                    className="absolute right-2 top-1/2 transform -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-red-50 rounded z-10"
                    title="Delete session"
                  >
                    {isDeleting === sessionId ? (
                      <RefreshCw className="w-3 h-3 animate-spin text-red-500" />
                    ) : (
                      <Trash2 className="w-3 h-3 text-red-500 hover:text-red-700" />
                    )}
                  </button>
                </div>
              ))}
            </SelectContent>
          </Select>

          {/* Show placeholder if no sessions */}
          {sessions.length === 0 && !isLoading && (
            <p className="text-xs text-gray-500 mt-1 text-center">No chat sessions yet</p>
          )}
        </div>

        {/* Current Active Session */}
        {currentSessionId && (
          <div className="space-y-2">
            <label className="text-xs text-gray-600">Current Active Session</label>
            <AnimatePresence>
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="flex items-center gap-3 p-3 rounded-lg border bg-blue-50 border-blue-200 shadow-sm"
              >
                <MessageCircle className="w-4 h-4 flex-shrink-0 text-blue-600" />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium truncate text-blue-900">
                    {formatSessionId(currentSessionId)}
                  </p>
                  <p className="text-xs text-blue-600 truncate">
                    ID: {currentSessionId.slice(-8)}
                  </p>
                </div>
                <div className="flex items-center gap-1 text-xs text-blue-600 font-medium">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  Active
                </div>
              </motion.div>
            </AnimatePresence>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="space-y-2">
            <div className="animate-pulse">
              <div className="h-16 bg-gray-200 rounded-lg"></div>
            </div>
          </div>
        )}

        {/* Session Statistics */}
        {sessions.length > 0 && (
          <div className="text-center">
            <p className="text-xs text-gray-500">
              {sessions.length} total session{sessions.length !== 1 ? 's' : ''} available
            </p>
          </div>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Chat Session</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this chat session? This action cannot be undone and all messages will be permanently removed.
            </AlertDialogDescription>
          </AlertDialogHeader>

          {sessionToDelete === currentSessionId && (
            <div className="mx-6 mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-800 text-sm">
              <span className="font-medium">⚠️ Warning:</span> This is your currently active session. Deleting it will clear your current conversation.
            </div>
          )}

          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDelete}
              className="bg-red-600 hover:bg-red-700 text-white"
              disabled={isDeleting === sessionToDelete}
            >
              {isDeleting === sessionToDelete ? (
                <div className="flex items-center gap-2">
                  <RefreshCw className="w-3 h-3 animate-spin" />
                  Deleting...
                </div>
              ) : (
                'Delete Session'
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
