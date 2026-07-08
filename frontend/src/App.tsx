import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { DashboardPage } from "@/features/dashboard/dashboard-page";
import { RoadmapListPage } from "@/features/roadmap/roadmap-list-page";
import { RoadmapDetailPage } from "@/features/roadmap/roadmap-detail-page";
import { QuizSessionPage } from "@/features/session/quiz-session-page";
import { CompetitivePage } from "@/features/competitive/competitive-page";
import { CompetitiveSessionPage } from "@/features/competitive/competitive-session-page";
import { AlgorithmFoundationsPage } from "@/features/algorithm-foundations/algorithm-foundations-page";
import { AlgorithmFoundationsUnitPage } from "@/features/algorithm-foundations/algorithm-foundations-unit-page";
import { AlgorithmFoundationsSessionPage } from "@/features/algorithm-foundations/algorithm-foundations-session-page";
import { SqlDojoPage } from "@/features/sql-dojo/sql-dojo-page";
import { SqlDojoSessionPage } from "@/features/sql-dojo/sql-dojo-session-page";

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/roadmaps" element={<RoadmapListPage />} />
          <Route
            path="/roadmaps/:roadmapId"
            element={<RoadmapDetailPage />}
          />
          <Route
            path="/sessions/:sessionId"
            element={<QuizSessionPage />}
          />
          <Route path="/algorithm-quiz" element={<CompetitivePage />} />
          <Route
            path="/algorithm-quiz/:sessionId"
            element={<CompetitiveSessionPage />}
          />
          <Route
            path="/algorithm-foundations"
            element={<AlgorithmFoundationsPage />}
          />
          <Route
            path="/algorithm-foundations/units/:unitId"
            element={<AlgorithmFoundationsUnitPage />}
          />
          <Route
            path="/algorithm-foundations/:sessionId"
            element={<AlgorithmFoundationsSessionPage />}
          />
          <Route path="/sql-dojo" element={<SqlDojoPage />} />
          <Route path="/sql-dojo/:sessionId" element={<SqlDojoSessionPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
