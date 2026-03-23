/**
 * MVVM command layer: same functions the Vue app and Vitest use (no onclick simulation).
 * Maps to chat.ui CapSpec request.command + params.
 */

export type ChatUiCommand = "chat.openWindow" | "chat.sendMessage" | "chat.refreshThread";

export interface ChatUiRequest {
  uiContext?: Record<string, unknown>;
  command: ChatUiCommand;
  params: Record<string, unknown>;
  sessionId?: string;
}

export function openWindowRequest(
  primaryContactId: string,
  context?: { kind?: string; entityId?: string },
): ChatUiRequest {
  return {
    uiContext: {},
    command: "chat.openWindow",
    params: {
      primaryContactId,
      context: context ?? {},
    },
  };
}

export function sendMessageRequest(text: string, sessionId?: string): ChatUiRequest {
  const r: ChatUiRequest = {
    uiContext: {},
    command: "chat.sendMessage",
    params: { text },
  };
  if (sessionId) r.sessionId = sessionId;
  return r;
}

export function refreshThreadRequest(sessionId?: string): ChatUiRequest {
  const r: ChatUiRequest = {
    uiContext: {},
    command: "chat.refreshThread",
    params: {},
  };
  if (sessionId) r.sessionId = sessionId;
  return r;
}
