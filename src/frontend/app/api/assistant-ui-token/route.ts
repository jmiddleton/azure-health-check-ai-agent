import { AssistantCloud } from "@assistant-ui/react";
import { auth } from "@clerk/nextjs/server";
 
export const POST = async (req: Request) => {
  const { userId, orgId } = await auth();
 
  if (!userId) throw new Error("User not authenticated");
 
  const workspaceId = orgId ? `${orgId}_${userId}` : userId;
  const assistantCloud = new AssistantCloud({
    apiKey: process.env["ASSISTANT_API_KEY"]!,
    userId,
    workspaceId,
  });
  const {token} = await assistantCloud.auth.tokens.create();

  return new Response(token);
};