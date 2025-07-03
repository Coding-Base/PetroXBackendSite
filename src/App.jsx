import AppProvider from './providers/AppProvider';
import AppRouter from './routes';
export default function App() {
  return (
    <AppProvider>
      <AppRouter />
    </AppProvider>
  );
}
