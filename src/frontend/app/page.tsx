"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import {
  ArrowRight,
  Activity,
  Brain,
  FileSpreadsheet,
  ShieldAlert,
  MessageSquare,
  Lock
} from "lucide-react";
import { DotBackground } from "@/components/dot-background";
import {
  SignInButton,
  SignUpButton,
  SignedIn,
  SignedOut,
  UserButton,
} from '@clerk/nextjs'

const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5 }
};

const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: 0.1
    }
  }
};

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-black text-white selection:bg-blue-500/30">
      <div className="relative z-10">
        {/* Navigation */}
        <nav className="flex items-center justify-between px-6 py-6 max-w-7xl mx-auto">
          <div className="text-xl font-bold tracking-tighter bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            Azure SRE Agent
          </div>

          <div className="flex gap-4 items-center">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/10 bg-white/5 text-sm text-gray-400 backdrop-blur-sm">
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

        {/* Dynamic Background */}
        <div className="fixed inset-0 -z-10 overflow-hidden">
          <div className="absolute inset-0 bg-black" />
          <DotBackground />
        </div>

        {/* Hero Section */}
        <section className="relative overflow-hidden px-6 py-20 md:py-32">
          <div className="mx-auto max-w-7xl text-center">
            <motion.div
              initial="initial"
              animate="animate"
              variants={staggerContainer}
              className="mx-auto max-w-4xl space-y-8"
            >
              <motion.h1
                variants={fadeInUp}
                className="bg-gradient-to-b from-white to-white/60 bg-clip-text text-5xl font-bold tracking-tight text-transparent sm:text-7xl"
              >
                Autonomous Health Checks for Azure Integration
              </motion.h1>

              <motion.p
                variants={fadeInUp}
                className="mx-auto max-w-2xl text-lg text-gray-400 sm:text-xl"
              >
                Automatically detect issues, summarize system health, and provide actionable insights 
                for Azure services. Powered by Microsoft Agent Framework and Azure Foundry.
              </motion.p>

              <motion.div
                variants={fadeInUp}
                className="flex flex-col items-center justify-center gap-4 sm:flex-row"
              >
                <Link href="/chat">
                  <Button
                    size="lg"
                    className="h-12 px-8 text-base bg-blue-600 hover:bg-blue-500 text-white border-0 shadow-[0_0_20px_rgba(37,99,235,0.3)]"
                  >
                    Start Health Check
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </Link>
              </motion.div>

              <div className="relative rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm overflow-hidden shadow-2xl">
                <div className="absolute inset-0 bg-gradient-to-b from-blue-500/10 via-transparent to-transparent z-10 pointer-events-none" />
                <div className="relative w-full mx-auto" style={{ aspectRatio: '16 / 9' }}>
                  <Image
                    src="/sre_chat.png"
                    alt="Azure Health Check Dashboard"
                    fill
                    sizes="(max-width: 768px) 100vw, (max-width: 1200px) 90vw, 1200px"
                    className="object-cover object-center rounded-2xl grayscale hover:grayscale-16 transition-all duration-500"
                    priority
                    quality={75}
                  />
                </div>
              </div>
            </motion.div>
          </div>
        </section>

        {/* Features Grid */}
        <section className="px-6 py-24 max-w-7xl mx-auto border-t border-white/10">
          <div className="max-w-3xl mx-auto text-center space-y-4 mb-16">
              <h2 className="bg-gradient-to-b from-white to-white/60 bg-clip-text text-5xl font-bold tracking-tight text-transparent sm:text-5xl">Intelligent Azure Monitoring</h2>
              <p className="text-lg text-muted-foreground">
                The AI Agent monitors Azure resources, detects anomalies, and uses artificial intelligence to suggest recommendations to fix issues. It supports natural language commands and interoperates with tools like Azure SDK and Azure Management API.
              </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            <FeatureCard
              icon={<Activity className="h-6 w-6 text-blue-400" />}
              title="Automated Health Checks"
              description="Periodically verifies the operational status of Azure Data Factory pipelines, Logic Apps, App Insights, and API integrations."
            />
            <FeatureCard
              icon={<Brain className="h-6 w-6 text-purple-400" />}
              title="Intelligent Error Analysis"
              description="Uses LLM to summarize failure messages, filter known/expected issues, and suggest resolutions for faster remediation."
            />
            <FeatureCard
              icon={<FileSpreadsheet className="h-6 w-6 text-green-400" />}
              title="Batch Processing"
              description="Reads health check definitions from CSV or Excel files to perform comprehensive checks on multiple resources."
            />
            <FeatureCard
              icon={<ShieldAlert className="h-6 w-6 text-red-400" />}
              title="Adaptive Filtering"
              description="Automatically ignores pre-defined false positives and learns from historical data to reduce alert fatigue."
            />
            <FeatureCard
              icon={<MessageSquare className="h-6 w-6 text-yellow-400" />}
              title="Natural Language Chat"
              description="Ask plain-language questions about your Azure resources and health status."
            />
            <FeatureCard
              icon={<Lock className="h-6 w-6 text-cyan-400" />}
              title="Secure & Integrated"
              description="Built with Microsoft Agent Framework. Supports Jira ticketing and Azure Dashboard reporting."
            />
          </div>
        </section>

        {/* Architecture Section */}
        <section className="px-6 py-24 max-w-7xl mx-auto border-t border-white/10">
          <div className="container">
            <div className="max-w-3xl mx-auto text-center space-y-4 mb-16">
              <h2 className="bg-gradient-to-b from-white to-white/60 bg-clip-text text-5xl font-bold tracking-tight text-transparent sm:text-5xl">Architecture</h2>
              <p className="text-lg text-muted-foreground">
                This solution deploys a web-based chat application with an AI agent running in Azure Container App, leveraging Azure AI Agent service with knowledge about issues and recommendations.
              </p>
            </div>

              <div className="relative w-full mx-auto rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm overflow-hidden shadow-2xl">
                  <div className="absolute inset-0 bg-gradient-to-b from-blue-500/10 via-transparent to-transparent z-10 pointer-events-none" />
                  <Image
                    src="/architecture.png"
                    alt="Azure Health Check Dashboard"
                    width={1300}
                    height={675}
                    className="object-cover object-center rounded-2xl transition-all duration-500"
                    priority
                  />
                </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t border-white/10 bg-black px-6 py-12 text-sm text-gray-500">
          <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-6 md:flex-row">
            <div className="flex items-center gap-2">
              <div className="h-6 w-6 rounded-full bg-white/20" />
              <span className="font-semibold text-white">Punta Negra</span>
            </div>

            <div className="flex gap-8">
              <Link href="#" className="hover:text-white">Twitter</Link>
              <Link href="#" className="hover:text-white">GitHub</Link>
              <Link href="#" className="hover:text-white">Discord</Link>
              <Link href="#" className="hover:text-white">LinkedIn</Link>
            </div>

            <p>© 2025 Punta Negra, Inc.</p>
          </div>
        </footer>
      </div>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="p-6 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors duration-300 backdrop-blur-sm">
      <div className="mb-4 p-3 rounded-xl bg-white/5 w-fit">{icon}</div>
      <h3 className="text-xl font-semibold mb-2 text-white">{title}</h3>
      <p className="text-gray-400 leading-relaxed">{description}</p>
    </div>
  );
}
