"use client"

import { useEffect, useRef } from 'react'

export function CloudBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const gl = canvas.getContext('webgl2') || canvas.getContext('webgl')
    if (!gl) return

    // Vertex shader
    const vertexShaderSource = `
      attribute vec2 a_position;
      void main() {
        gl_Position = vec4(a_position, 0.0, 1.0);
      }
    `

    // Fragment shader with cloud effect
    const fragmentShaderSource = `
      precision highp float;

      uniform vec2 u_resolution;
      uniform float u_time;

      const float cloudscale = 1.1;
      const float speed = 0.03;
      const float clouddark = 0.5;
      const float cloudlight = 0.3;
      const float cloudcover = 0.2;
      const float cloudalpha = 8.0;
      const float skytint = 0.5;
      const vec3 skycolour1 = vec3(0.2, 0.4, 0.6);
      const vec3 skycolour2 = vec3(0.4, 0.7, 1.0);

      const mat2 m = mat2(1.6, 1.2, -1.2, 1.6);

      vec2 hash(vec2 p) {
        p = vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3)));
        return -1.0 + 2.0 * fract(sin(p) * 43758.5453123);
      }

      float noise(in vec2 p) {
        const float K1 = 0.366025404;
        const float K2 = 0.211324865;
        vec2 i = floor(p + (p.x + p.y) * K1);
        vec2 a = p - i + (i.x + i.y) * K2;
        vec2 o = (a.x > a.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
        vec2 b = a - o + K2;
        vec2 c = a - 1.0 + 2.0 * K2;
        vec3 h = max(0.5 - vec3(dot(a, a), dot(b, b), dot(c, c)), 0.0);
        vec3 n = h * h * h * h * vec3(dot(a, hash(i + 0.0)), dot(b, hash(i + o)), dot(c, hash(i + 1.0)));
        return dot(n, vec3(70.0));
      }

      float fbm(vec2 n) {
        float total = 0.0, amplitude = 0.1;
        for (int i = 0; i < 7; i++) {
          total += noise(n) * amplitude;
          n = m * n;
          amplitude *= 0.4;
        }
        return total;
      }

      void main() {
        vec2 fragCoord = gl_FragCoord.xy;
        vec2 p = fragCoord / u_resolution;
        vec2 uv = p * vec2(u_resolution.x / u_resolution.y, 1.0);
        float time = u_time * speed;
        float q = fbm(uv * cloudscale * 0.5);

        float r = 0.0;
        uv *= cloudscale;
        uv -= q - time;
        float weight = 0.8;
        for (int i = 0; i < 8; i++) {
          r += abs(weight * noise(uv));
          uv = m * uv + time;
          weight *= 0.7;
        }

        float f = 0.0;
        uv = p * vec2(u_resolution.x / u_resolution.y, 1.0);
        uv *= cloudscale;
        uv -= q - time;
        weight = 0.7;
        for (int i = 0; i < 8; i++) {
          f += weight * noise(uv);
          uv = m * uv + time;
          weight *= 0.6;
        }

        f *= r + f;

        float c = 0.0;
        time = u_time * speed * 2.0;
        uv = p * vec2(u_resolution.x / u_resolution.y, 1.0);
        uv *= cloudscale * 2.0;
        uv -= q - time;
        weight = 0.4;
        for (int i = 0; i < 7; i++) {
          c += weight * noise(uv);
          uv = m * uv + time;
          weight *= 0.6;
        }

        float c1 = 0.0;
        time = u_time * speed * 3.0;
        uv = p * vec2(u_resolution.x / u_resolution.y, 1.0);
        uv *= cloudscale * 3.0;
        uv -= q - time;
        weight = 0.4;
        for (int i = 0; i < 7; i++) {
          c1 += abs(weight * noise(uv));
          uv = m * uv + time;
          weight *= 0.6;
        }

        c += c1;

        vec3 skycolour = mix(skycolour2, skycolour1, p.y);
        vec3 cloudcolour = vec3(1.1, 1.1, 0.9) * clamp((clouddark + cloudlight * c), 0.0, 1.0);

        f = cloudcover + cloudalpha * f * r;

        vec3 result = mix(skycolour, clamp(skytint * skycolour + cloudcolour, 0.0, 1.0), clamp(f + c, 0.0, 1.0));

        gl_FragColor = vec4(result, 1.0);
      }
    `

    // Create shaders
    const createShader = (gl: WebGLRenderingContext, type: number, source: string) => {
      const shader = gl.createShader(type)
      if (!shader) return null
      gl.shaderSource(shader, source)
      gl.compileShader(shader)
      if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
        console.error('Shader compile error:', gl.getShaderInfoLog(shader))
        gl.deleteShader(shader)
        return null
      }
      return shader
    }

    const vertexShader = createShader(gl, gl.VERTEX_SHADER, vertexShaderSource)
    const fragmentShader = createShader(gl, gl.FRAGMENT_SHADER, fragmentShaderSource)

    if (!vertexShader || !fragmentShader) return

    // Create program
    const program = gl.createProgram()
    if (!program) return

    gl.attachShader(program, vertexShader)
    gl.attachShader(program, fragmentShader)
    gl.linkProgram(program)

    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      console.error('Program link error:', gl.getProgramInfoLog(program))
      return
    }

    // Set up geometry
    const positionBuffer = gl.createBuffer()
    gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer)
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([
      -1, -1, 1, -1, -1, 1,
      -1, 1, 1, -1, 1, 1
    ]), gl.STATIC_DRAW)

    const positionLocation = gl.getAttribLocation(program, 'a_position')
    const resolutionLocation = gl.getUniformLocation(program, 'u_resolution')
    const timeLocation = gl.getUniformLocation(program, 'u_time')

    // Resize canvas
    const resize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
      gl.viewport(0, 0, canvas.width, canvas.height)
    }
    resize()
    window.addEventListener('resize', resize)

    // Animation loop
    let startTime = Date.now()
    const animate = () => {
      const time = (Date.now() - startTime) / 1000

      gl.clearColor(0, 0, 0, 1)
      gl.clear(gl.COLOR_BUFFER_BIT)

      gl.useProgram(program)

      gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer)
      gl.enableVertexAttribArray(positionLocation)
      gl.vertexAttribPointer(positionLocation, 2, gl.FLOAT, false, 0, 0)

      gl.uniform2f(resolutionLocation, canvas.width, canvas.height)
      gl.uniform1f(timeLocation, time)

      gl.drawArrays(gl.TRIANGLES, 0, 6)

      requestAnimationFrame(animate)
    }
    animate()

    return () => {
      window.removeEventListener('resize', resize)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 -z-20 w-full h-full"
      style={{ opacity: 0.8 }}
    />
  )
}
