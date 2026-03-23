import { describe, expect, it } from "vitest";
import {
  openWindowRequest,
  refreshThreadRequest,
  sendMessageRequest,
} from "../src/commands/chatCommands";

describe("chatCommands (MVVM)", () => {
  it("builds chat.openWindow payload", () => {
    const r = openWindowRequest("con-1", { kind: "supplier", entityId: "s1" });
    expect(r.command).toBe("chat.openWindow");
    expect(r.params).toEqual({
      primaryContactId: "con-1",
      context: { kind: "supplier", entityId: "s1" },
    });
  });

  it("builds chat.sendMessage with optional sessionId", () => {
    const r = sendMessageRequest("hi", "sess-9");
    expect(r.command).toBe("chat.sendMessage");
    expect(r.params).toEqual({ text: "hi" });
    expect(r.sessionId).toBe("sess-9");
  });

  it("builds chat.refreshThread", () => {
    const r = refreshThreadRequest();
    expect(r.command).toBe("chat.refreshThread");
  });
});
