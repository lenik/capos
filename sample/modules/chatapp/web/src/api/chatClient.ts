/** HTTP bridge to Python chatsessionmgr via POST /api/chat/ui */

export async function postChatUi(
  baseUrl: string,
  body: Record<string, unknown>,
): Promise<{
  viewModel: Record<string, unknown>;
  lastResult: { ok: boolean; detail?: string };
}> {
  const root = baseUrl.replace(/\/$/, "");
  const url = `${root}/api/chat/ui`;
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    const t = await r.text();
    throw new Error(`chat.ui HTTP ${r.status}: ${t}`);
  }
  return r.json() as Promise<{
    viewModel: Record<string, unknown>;
    lastResult: { ok: boolean; detail?: string };
  }>;
}
