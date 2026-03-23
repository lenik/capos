<script setup lang="ts">
import { ref } from "vue";
import { postChatUi } from "./api/chatClient";
import { openWindowRequest, sendMessageRequest, refreshThreadRequest } from "./commands/chatCommands";

const baseUrl = ref(import.meta.env.VITE_CHATAPP_API || "");
const log = ref<string[]>([]);
const busy = ref(false);

async function runOpen() {
  busy.value = true;
  try {
    const body = openWindowRequest("con-100", { kind: "supplier", entityId: "sup-1" });
    const out = await postChatUi(baseUrl.value, body);
    log.value.push(JSON.stringify(out.lastResult));
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <main style="font-family: system-ui; padding: 1rem">
    <h1>chatweb</h1>
    <p>MVVM commands live in <code>src/commands/</code>; tests use the same modules (no synthetic DOM events).</p>
    <label>API base <input v-model="baseUrl" placeholder="http://127.0.0.1:PORT" size="40" /></label>
    <p><button :disabled="busy" @click="runOpen">openWindow (demo)</button></p>
    <pre>{{ log.join("\n") }}</pre>
  </main>
</template>
