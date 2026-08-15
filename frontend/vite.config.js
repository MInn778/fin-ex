import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: Number(process.env.FRONTEND_PORT) || 3000,
    proxy: {
      // TODO: 팀 오케스트레이션 구조가 정해지면 backend(오케스트레이터)로 옮길 수 있음.
      // 지금은 db-api가 /api/analyze, /api/reports를 직접 처리함.
      "/api": {
        target: `http://localhost:${process.env.DB_API_PORT || 8081}`,
        changeOrigin: true,
      },
    },
  },
});
