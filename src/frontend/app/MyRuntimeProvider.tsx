"use client";

import type { ReactNode } from "react";
import {
    AssistantRuntimeProvider,
    ChatModelRunResult,
    useLocalRuntime,
    type ChatModelAdapter,
} from "@assistant-ui/react";
import { AssistantCloud } from "assistant-cloud";

export const FastAPIAdapter: ChatModelAdapter = {
    async *run({ messages, abortSignal }) {
        const apiUrl = process.env["API_HEALTHCHECK_BASE_URL"] || "http://localhost:8000";
        const response = await fetch(apiUrl + "/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            // USER ID Should come from authenticated user context
            body: JSON.stringify({ messages, user_id: "user-123", thread_id: "test-123" }),
            signal: abortSignal,
        });


        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body!.getReader();
        const decoder = new TextDecoder();
        let accumulatedContent = "";
        let chartEmitted = false;

        const tryParseJsonFromString = (s: string) => {
            const trimmed = s.trim();
            // strip markdown code fences if present
            const fenceMatch = trimmed.match(/```(?:json)?\n([\s\S]*)\n```$/i);
            const candidate = fenceMatch ? fenceMatch[1].trim() : trimmed;

            try {
                if (candidate.startsWith("{") || candidate.startsWith("[")) {
                    return JSON.parse(candidate);
                }
            } catch (e) {
                // try to locate a JSON substring between first { and last }
                const first = candidate.indexOf("{");
                const last = candidate.lastIndexOf("}");
                if (first !== -1 && last !== -1 && last > first) {
                    try {
                        const sub = candidate.substring(first, last + 1);
                        return JSON.parse(sub);
                    } catch (e) {
                        return null;
                    }
                }
            }

            return null;
        };

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const events = chunk.split("\n\n").filter(Boolean);

            for (const event of events) {
                try {
                    const jsonStr = event.replace(/^data: /, "").trim();
                    const data = JSON.parse(jsonStr);
                    accumulatedContent += data.content + ""; // Accumulate content
                    console.log("Received chunk:", accumulatedContent);

                    // If we've already emitted a chart for this run, continue emitting text updates only
                    if (!chartEmitted) {
                        const parsed = tryParseJsonFromString(accumulatedContent);
                        if (parsed) {
                            // emit as a text code fence so the frontend markdown renderer can render it safely
                            const code = "```chart\n" + JSON.stringify(parsed) + "\n```";
                            const result: ChatModelRunResult = {
                                content: [{ type: "text", text: code }],
                            };
                            chartEmitted = true;
                            yield result;
                            continue;
                        }
                    }

                    // fallback: emit accumulated text so the user sees progressive updates
                    const result: ChatModelRunResult = {
                        content: [{ type: "text", text: accumulatedContent.trim() }],
                    };
                    yield result;
                } catch (error) {
                }
            }
        }
    },
};

export function MyRuntimeProvider({
    children,
}: Readonly<{
    children: ReactNode;
}>) {
    const cloud = new AssistantCloud({
        baseUrl: process.env["NEXT_PUBLIC_ASSISTANT_BASE_URL"]!,
        anonymous: true,
    });

    const runtime = useLocalRuntime(FastAPIAdapter, {
        cloud, // Enables multi-thread support
    });

    return (
        <AssistantRuntimeProvider runtime={runtime}>
            {children}
        </AssistantRuntimeProvider>
    );
}
