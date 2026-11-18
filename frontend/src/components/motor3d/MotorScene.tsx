import React, { useRef, useState } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import * as THREE from 'three'

export interface MotorComponentStatus {
  key: string
  name: string
  status: 'normal' | 'warning' | 'critical'
  metricLabel?: string
  metricValue?: string
}

interface MotorSceneProps {
  activeFault?: string | null
  selectedComponentKey?: string | null
  onSelectComponent?: (key: string) => void
  componentStatuses?: Record<string, MotorComponentStatus>
  exploded?: boolean
  isRunning?: boolean
}

// Subcomponent: Motor Shaft
const Shaft: React.FC<{
  isRunning?: boolean
  exploded?: boolean
  isSelected?: boolean
  onClick?: () => void
  onPointerOver?: () => void
  onPointerOut?: () => void
  status?: 'normal' | 'warning' | 'critical'
}> = ({ isRunning, isSelected, onClick, onPointerOver, onPointerOut, status }) => {
  const meshRef = useRef<THREE.Mesh>(null)

  useFrame((_, delta) => {
    if (isRunning && meshRef.current) {
      meshRef.current.rotation.x += delta * 8
    }
  })

  const color = isSelected ? '#FF5A36' : status === 'critical' ? '#FF5A36' : '#FFFFFF'

  return (
    <mesh
      ref={meshRef}
      rotation={[0, 0, Math.PI / 2]}
      position={[0, 0, 0]}
      onClick={(e) => {
        e.stopPropagation()
        onClick?.()
      }}
      onPointerOver={(e) => {
        e.stopPropagation()
        onPointerOver?.()
      }}
      onPointerOut={onPointerOut}
    >
      <cylinderGeometry args={[0.22, 0.22, 4.2, 32]} />
      <meshStandardMaterial
        color={color}
        metalness={0.85}
        roughness={0.2}
        emissive={isSelected ? '#FF5A36' : '#000000'}
        emissiveIntensity={isSelected ? 0.3 : 0}
      />
    </mesh>
  )
}

// Subcomponent: Bearings (Drive-end front & Rear)
const Bearing: React.FC<{
  position: [number, number, number]
  name: string
  status?: 'normal' | 'warning' | 'critical'
  isSelected?: boolean
  onClick?: () => void
  onPointerOver?: () => void
  onPointerOut?: () => void
}> = ({ position, isSelected, status, onClick, onPointerOver, onPointerOut }) => {
  const meshRef = useRef<THREE.Mesh>(null)

  useFrame(({ clock }) => {
    if (status === 'critical' && meshRef.current) {
      const pulse = (Math.sin(clock.getElapsedTime() * 6) + 1) / 2
      ;(meshRef.current.material as THREE.MeshStandardMaterial).emissiveIntensity =
        0.3 + pulse * 0.7
    }
  })

  const baseColor =
    status === 'critical'
      ? '#FF5A36'
      : status === 'warning'
        ? '#FFFFFF'
        : isSelected
          ? '#FF5A36'
          : '#FFFFFF'

  const emissiveColor = status === 'critical' ? '#FF5A36' : isSelected ? '#FF5A36' : '#000000'

  return (
    <group position={position}>
      {/* Outer race */}
      <mesh
        ref={meshRef}
        rotation={[0, 0, Math.PI / 2]}
        onClick={(e) => {
          e.stopPropagation()
          onClick?.()
        }}
        onPointerOver={(e) => {
          e.stopPropagation()
          onPointerOver?.()
        }}
        onPointerOut={onPointerOut}
      >
        <torusGeometry args={[0.42, 0.12, 16, 32]} />
        <meshStandardMaterial
          color={baseColor}
          metalness={0.9}
          roughness={0.15}
          emissive={emissiveColor}
          emissiveIntensity={status === 'critical' ? 0.6 : isSelected ? 0.4 : 0}
        />
      </mesh>
    </group>
  )
}

// Subcomponent: Rotor Core
const RotorCore: React.FC<{
  isRunning?: boolean
  isSelected?: boolean
  onClick?: () => void
  onPointerOver?: () => void
  onPointerOut?: () => void
}> = ({ isRunning, isSelected, onClick, onPointerOver, onPointerOut }) => {
  const rotorRef = useRef<THREE.Group>(null)

  useFrame((_, delta) => {
    if (isRunning && rotorRef.current) {
      rotorRef.current.rotation.x += delta * 8
    }
  })

  return (
    <group
      ref={rotorRef}
      rotation={[0, 0, Math.PI / 2]}
      onClick={(e) => {
        e.stopPropagation()
        onClick?.()
      }}
      onPointerOver={(e) => {
        e.stopPropagation()
        onPointerOver?.()
      }}
      onPointerOut={onPointerOut}
    >
      <mesh>
        <cylinderGeometry args={[0.62, 0.62, 1.6, 24]} />
        <meshStandardMaterial
          color={isSelected ? '#FF5A36' : '#FFFFFF'}
          metalness={0.8}
          roughness={0.4}
        />
      </mesh>
    </group>
  )
}

// Subcomponent: Copper Stator Windings
const StatorWindings: React.FC<{
  status?: 'normal' | 'warning' | 'critical'
  isSelected?: boolean
  exploded?: boolean
  onClick?: () => void
  onPointerOver?: () => void
  onPointerOut?: () => void
}> = ({ status, isSelected, exploded, onClick, onPointerOver, onPointerOut }) => {
  const meshRef = useRef<THREE.Mesh>(null)

  useFrame(({ clock }) => {
    if (status === 'critical' && meshRef.current) {
      const pulse = (Math.sin(clock.getElapsedTime() * 5) + 1) / 2
      ;(meshRef.current.material as THREE.MeshStandardMaterial).emissiveIntensity =
        0.4 + pulse * 0.6
    }
  })

  const baseColor =
    status === 'critical'
      ? '#FF5A36'
      : status === 'warning'
        ? '#FFFFFF'
        : isSelected
          ? '#FF5A36'
          : '#FFFFFF'

  const emissiveColor = status === 'critical' ? '#FF5A36' : isSelected ? '#FF5A36' : '#000000'

  return (
    <mesh
      ref={meshRef}
      rotation={[0, 0, Math.PI / 2]}
      position={[0, exploded ? 0.6 : 0, 0]}
      onClick={(e) => {
        e.stopPropagation()
        onClick?.()
      }}
      onPointerOver={(e) => {
        e.stopPropagation()
        onPointerOver?.()
      }}
      onPointerOut={onPointerOut}
    >
      <cylinderGeometry args={[0.92, 0.92, 1.7, 32, 1, true]} />
      <meshStandardMaterial
        color={baseColor}
        metalness={0.7}
        roughness={0.25}
        emissive={emissiveColor}
        emissiveIntensity={status === 'critical' ? 0.6 : 0.2}
        side={THREE.DoubleSide}
      />
    </mesh>
  )
}

// Subcomponent: Main Cast Frame Housing & Cooling Fins
const MotorHousing: React.FC<{
  status?: 'normal' | 'warning' | 'critical'
  isSelected?: boolean
  exploded?: boolean
  onClick?: () => void
  onPointerOver?: () => void
  onPointerOut?: () => void
}> = ({ isSelected, exploded, onClick, onPointerOver, onPointerOut }) => {
  return (
    <group
      position={[0, exploded ? 1.4 : 0, 0]}
      onClick={(e) => {
        e.stopPropagation()
        onClick?.()
      }}
      onPointerOver={(e) => {
        e.stopPropagation()
        onPointerOver?.()
      }}
      onPointerOut={onPointerOut}
    >
      {/* Semi-transparent outer cutaway cylinder */}
      <mesh rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[1.15, 1.15, 2.1, 32, 1, true, 0, Math.PI * 1.55]} />
        <meshStandardMaterial
          color={isSelected ? '#FF5A36' : '#000000'}
          metalness={0.6}
          roughness={0.4}
          side={THREE.DoubleSide}
          transparent
          opacity={exploded ? 0.4 : 0.75}
        />
      </mesh>

      {/* External Cooling Fins */}
      {Array.from({ length: 8 }).map((_, i) => {
        const angle = (i * Math.PI * 1.5) / 8
        const y = Math.cos(angle) * 1.22
        const z = Math.sin(angle) * 1.22
        return (
          <mesh key={i} position={[0, y, z]} rotation={[angle, 0, 0]}>
            <boxGeometry args={[2.0, 0.05, 0.18]} />
            <meshStandardMaterial color="#FFFFFF" metalness={0.5} roughness={0.5} />
          </mesh>
        )
      })}

      {/* Terminal Box */}
      <mesh position={[0, 1.45, 0]}>
        <boxGeometry args={[0.65, 0.35, 0.55]} />
        <meshStandardMaterial color="#000000" metalness={0.6} roughness={0.3} />
      </mesh>

      {/* Mounting Feet Base */}
      <mesh position={[0, -1.25, 0]}>
        <boxGeometry args={[1.8, 0.15, 1.6]} />
        <meshStandardMaterial color="#000000" metalness={0.7} roughness={0.4} />
      </mesh>
    </group>
  )
}

// Subcomponent: Rear Cooling Fan
const CoolingFan: React.FC<{
  isRunning?: boolean
  isSelected?: boolean
  exploded?: boolean
  status?: 'normal' | 'warning' | 'critical'
  onClick?: () => void
  onPointerOver?: () => void
  onPointerOut?: () => void
}> = ({ isRunning, isSelected, exploded, onClick, onPointerOver, onPointerOut }) => {
  const fanRef = useRef<THREE.Group>(null)

  useFrame((_, delta) => {
    if (isRunning && fanRef.current) {
      fanRef.current.rotation.x += delta * 8
    }
  })

  return (
    <group
      position={[exploded ? -2.2 : -1.4, 0, 0]}
      onClick={(e) => {
        e.stopPropagation()
        onClick?.()
      }}
      onPointerOver={(e) => {
        e.stopPropagation()
        onPointerOver?.()
      }}
      onPointerOut={onPointerOut}
    >
      <group ref={fanRef}>
        <mesh rotation={[0, 0, Math.PI / 2]}>
          <cylinderGeometry args={[0.3, 0.3, 0.2, 16]} />
          <meshStandardMaterial color="#FFFFFF" metalness={0.4} roughness={0.4} />
        </mesh>
        {Array.from({ length: 6 }).map((_, i) => {
          const angle = (i * Math.PI) / 3
          return (
            <mesh key={i} rotation={[angle, 0, 0]} position={[0, 0, 0]}>
              <boxGeometry args={[0.15, 0.8, 0.08]} />
              <meshStandardMaterial
                color={isSelected ? '#FF5A36' : '#FFFFFF'}
                roughness={0.3}
              />
            </mesh>
          )
        })}
      </group>
    </group>
  )
}

export const MotorScene: React.FC<MotorSceneProps> = ({
  selectedComponentKey,
  onSelectComponent,
  componentStatuses = {},
  exploded = false,
  isRunning = true,
}) => {
  const [hoveredComponent, setHoveredComponent] = useState<string | null>(null)

  const getStatus = (key: string): 'normal' | 'warning' | 'critical' => {
    return componentStatuses[key]?.status || 'normal'
  }

  const activeHover = hoveredComponent || selectedComponentKey

  return (
    <div className="relative h-[420px] w-full overflow-hidden rounded-xl border border-slate-800 bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 shadow-2xl select-none">
      {/* Overlay controls and legend */}
      <div className="pointer-events-none absolute top-4 left-4 z-10 flex flex-col gap-2">
        <div className="inline-flex items-center gap-2 rounded-full border border-slate-700 bg-slate-900/80 px-3 py-1.5 font-mono text-xs text-cyan-400 backdrop-blur-md">
          <span
            className={`h-2 w-2 rounded-full ${isRunning ? 'animate-pulse bg-emerald-400' : 'bg-slate-500'}`}
          />
          {isRunning ? 'MOTOR ROTATING (1450 RPM)' : 'MOTOR STOPPED'}
        </div>
        {activeHover && componentStatuses[activeHover] && (
          <div className="glass-panel animate-in fade-in rounded-xl border-cyan-400/40 p-3 text-xs shadow-2xl backdrop-blur-xl duration-150">
            <div className="font-semibold text-white drop-shadow-sm">
              {componentStatuses[activeHover].name}
            </div>
            {componentStatuses[activeHover].metricLabel && (
              <div className="mt-0.5 font-mono text-cyan-300">
                {componentStatuses[activeHover].metricLabel}:{' '}
                {componentStatuses[activeHover].metricValue}
              </div>
            )}
            <div className="mt-1 flex items-center gap-1.5">
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  componentStatuses[activeHover].status === 'critical'
                    ? 'bg-rose-400 animate-pulse'
                    : componentStatuses[activeHover].status === 'warning'
                      ? 'bg-amber-400 animate-pulse'
                      : 'bg-emerald-400 animate-pulse'
                }`}
              />
              <span className="font-mono text-[10px] tracking-wider text-slate-300 uppercase">
                Status: {componentStatuses[activeHover].status}
              </span>
            </div>
          </div>
        )}
      </div>

      <div className="pointer-events-none absolute right-4 bottom-3 z-10 glass-pill font-mono text-[11px] text-slate-300 backdrop-blur-md">
        Drag to Orbit • Scroll to Zoom • Click parts to inspect
      </div>

      <Canvas camera={{ position: [3.8, 2.5, 3.8], fov: 45 }}>
        <ambientLight intensity={0.9} />
        <directionalLight position={[10, 10, 5]} intensity={1.4} />
        <directionalLight position={[-10, -5, -5]} intensity={0.6} color="#FFFFFF" />
        <pointLight position={[0, 0, 0]} intensity={1.2} color="#FFFFFF" distance={4} />

        <group position={[0, -0.2, 0]}>
          {/* Shaft */}
          <Shaft
            isRunning={isRunning}
            isSelected={selectedComponentKey === 'shaft'}
            status={getStatus('shaft')}
            onClick={() => onSelectComponent?.('shaft')}
            onPointerOver={() => setHoveredComponent('shaft')}
            onPointerOut={() => setHoveredComponent(null)}
          />

          {/* Drive-End Front Bearing */}
          <Bearing
            position={[exploded ? 2.1 : 1.3, 0, 0]}
            name="Front Drive-End Bearing"
            status={getStatus('bearing_front')}
            isSelected={selectedComponentKey === 'bearing_front'}
            onClick={() => onSelectComponent?.('bearing_front')}
            onPointerOver={() => setHoveredComponent('bearing_front')}
            onPointerOut={() => setHoveredComponent(null)}
          />

          {/* Non-Drive-End Rear Bearing */}
          <Bearing
            position={[exploded ? -1.8 : -1.1, 0, 0]}
            name="Rear Non-Drive-End Bearing"
            status={getStatus('bearing_rear')}
            isSelected={selectedComponentKey === 'bearing_rear'}
            onClick={() => onSelectComponent?.('bearing_rear')}
            onPointerOver={() => setHoveredComponent('bearing_rear')}
            onPointerOut={() => setHoveredComponent(null)}
          />

          {/* Rotor Core */}
          <RotorCore
            isRunning={isRunning}
            isSelected={selectedComponentKey === 'rotor'}
            onClick={() => onSelectComponent?.('rotor')}
            onPointerOver={() => setHoveredComponent('rotor')}
            onPointerOut={() => setHoveredComponent(null)}
          />

          {/* Copper Stator Windings */}
          <StatorWindings
            status={getStatus('stator')}
            isSelected={selectedComponentKey === 'stator'}
            exploded={exploded}
            onClick={() => onSelectComponent?.('stator')}
            onPointerOver={() => setHoveredComponent('stator')}
            onPointerOut={() => setHoveredComponent(null)}
          />

          {/* Outer Housing & Cooling Fins */}
          <MotorHousing
            isSelected={selectedComponentKey === 'motor_casing'}
            exploded={exploded}
            onClick={() => onSelectComponent?.('motor_casing')}
            onPointerOver={() => setHoveredComponent('motor_casing')}
            onPointerOut={() => setHoveredComponent(null)}
          />

          {/* Rear Cooling Fan */}
          <CoolingFan
            isRunning={isRunning}
            isSelected={selectedComponentKey === 'cooling_fan'}
            exploded={exploded}
            status={getStatus('cooling_fan')}
            onClick={() => onSelectComponent?.('cooling_fan')}
            onPointerOver={() => setHoveredComponent('cooling_fan')}
            onPointerOut={() => setHoveredComponent(null)}
          />
        </group>

        <OrbitControls
          enablePan={true}
          enableZoom={true}
          enableRotate={true}
          maxDistance={10}
          minDistance={1.8}
        />
      </Canvas>
    </div>
  )
}

export default MotorScene
