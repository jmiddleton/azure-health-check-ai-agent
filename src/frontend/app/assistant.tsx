"use client";

import { AssistantRuntimeProvider, useLocalRuntime } from "@assistant-ui/react";
import {
  useChatRuntime,
  AssistantChatTransport,
} from "@assistant-ui/react-ai-sdk";
import { Thread } from "@/components/assistant-ui/thread";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { ThreadListSidebar } from "@/components/assistant-ui/threadlist-sidebar";
import { Separator } from "@/components/ui/separator";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { FastAPIAdapter } from "./components/MyRuntimeProvider";

export const Assistant = () => {
  // const runtime = useChatRuntime({
  //   transport: new AssistantChatTransport({
  //     api: "/api/chat",
  //   }),
  // }
  const runtime = useLocalRuntime(FastAPIAdapter);

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <SidebarProvider>
        <div className="flex h-[calc(100dvh-73px)] w-full pr-0.5">
          <ThreadListSidebar className="bg-background/80 backdrop-blur-sm border-r border-border" />
          <SidebarInset className="bg-transparent">
            <div className="flex-1 overflow-hidden">
              <Thread />
            </div>
          </SidebarInset>
        </div>
      </SidebarProvider>
    </AssistantRuntimeProvider>
  );
};
