"use client";

import { Assistant } from "../assistant";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { MyRuntimeProvider } from "../MyRuntimeProvider";

import {
  SignInButton,
  SignUpButton,
  SignedIn,
  SignedOut,
  UserButton,
} from '@clerk/nextjs'

export default function ChatPage() {
  return (
    <div className="min-h-screen bg-background text-foreground selection:bg-blue-500/30">
      <MyRuntimeProvider>
        {/* Navigation */}
        <nav className="relative z-10 flex items-center justify-between px-6 py-4 border-b border-border bg-background/80 backdrop-blur-sm">
          <Link href="/" className="text-xl font-bold tracking-tighter bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            Azure SRE Agent
          </Link>

          <div className="flex gap-4 items-center">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-border bg-muted/50 text-sm text-muted-foreground backdrop-blur-sm">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
              </span>
              System Operational
            </div>

            <SignedOut>
              <SignInButton />
              <SignUpButton>
                <button className="bg-[#6c47ff] text-white rounded-full font-medium text-sm sm:text-base h-10 sm:h-12 px-4 sm:px-5 cursor-pointer">
                  Sign Up
                </button>
              </SignUpButton>
            </SignedOut>
            <SignedIn>
              <UserButton />
            </SignedIn>
          </div>
        </nav>

        {/* Chat Interface */}
        <div className="relative z-10">
          <Assistant />
        </div>
      </MyRuntimeProvider>
    </div>
  );
}