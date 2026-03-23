/**
 * Integration: hits a live Python /api/chat/ui (MemCOS + chatsessionmgr) when CHATAPP_TEST_URL is set.
 * Run from repo: pytest sample/modules/chatapp/tests/test_chatapp_web_e2e.py (starts server + vitest).
 */
import { describe, expect, it } from "vitest";
import { postChatUi } from "../src/api/chatClient";
import { openWindowRequest, sendMessageRequest } from "../src/commands/chatCommands";

const base = process.env.CHATAPP_TEST_URL || "";

describe.skipIf(!base)("chat.ui HTTP (integration)", () => {
  it("openWindow and sendMessage against memcos-backed server", async () => {
    const open = await postChatUi(base, openWindowRequest("con-100", { kind: "supplier", entityId: "sup-1" }));
    expect(open.lastResult.ok).toBe(true);
    const sid = (open.viewModel.sessionId as string) || "";
    expect(sid.length).toBeGreaterThan(0);

    const sent = await postChatUi(base, sendMessageRequest("MVVM integration", sid));
    expect(sent.lastResult.ok).toBe(true);
    const bodies = (sent.viewModel.messages as { body: string }[]).map((m) => m.body);
    expect(bodies).toContain("MVVM integration");
  });
});

