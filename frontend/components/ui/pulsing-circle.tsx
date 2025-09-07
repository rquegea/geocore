"use client"

import { PulsingBorder } from "@paper-design/shaders-react"
import { motion } from "framer-motion"

export default function PulsingCircle({ position = "corner", size = 96 }: { position?: "corner" | "center"; size?: number }) {
  const containerClass = position === "center" ? `relative` : `absolute bottom-8 right-8 z-30`
  const boxStyle: React.CSSProperties = position === "center" ? { width: size, height: size } : { width: 80, height: 80 }
  return (
    <div className={containerClass}>
      <div className="relative flex items-center justify-center" style={boxStyle}>
        {/* Pulsing Border Circle */}
        <PulsingBorder
          colors={["#00E5FF", "#FF00A8", "#FF3B30", "#00FF88", "#FFD000", "#FF6B35", "#8A2BE2"]}
          colorBack="#00000000"
          speed={1.5}
          roundness={1}
          thickness={0.1}
          softness={0.15}
          intensity={8}
          spotsPerColor={5}
          spotSize={0.1}
          pulse={0.1}
          smoke={0.5}
          smokeSize={4}
          scale={0.75}
          rotation={0}
          frame={9161408.251009725}
          style={{
            width: position === "center" ? `${size * 0.7}px` : "60px",
            height: position === "center" ? `${size * 0.7}px` : "60px",
            borderRadius: "50%",
          }}
        />

        {/* Rotating Text Around the Pulsing Border */}
        <motion.svg
          className="absolute inset-0 w-full h-full"
          viewBox="0 0 100 100"
          animate={{ rotate: 360 }}
          transition={{
            duration: 20,
            repeat: Number.POSITIVE_INFINITY,
            ease: "linear",
          }}
          style={{ transform: "scale(1.6)" }}
        >
          <defs>
            <path id="circle" d="M 50, 50 m -38, 0 a 38,38 0 1,1 76,0 a 38,38 0 1,1 -76,0" />
          </defs>
          <text className="text-sm fill-white/80 instrument">
            <textPath href="#circle" startOffset="0%">
              t&tech is amazing • t&tech is amazing • t&tech is amazing • t&tech is amazing •
            </textPath>
          </text>
        </motion.svg>
      </div>
    </div>
  )
}
