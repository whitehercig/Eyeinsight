import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AppProvider } from "./context/AppContext";
import HomePage from "./pages/HomePage";
import ConsentPage from "./pages/ConsentPage";
import ScreeningPage from "./pages/ScreeningPage";
import LoadingAnalysisPage from "./pages/LoadingAnalysisPage";
import ResultPage from "./pages/ResultPage";

export default function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/"                      element={<HomePage />} />
          <Route path="/consent"               element={<ConsentPage />} />
          <Route path="/screening"             element={<ScreeningPage />} />
          <Route path="/analyzing/:sessionId"  element={<LoadingAnalysisPage />} />
          <Route path="/result/:sessionId"     element={<ResultPage />} />
          <Route path="*"                      element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AppProvider>
  );
}
