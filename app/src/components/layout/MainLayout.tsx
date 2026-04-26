import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopBar from './TopBar';

export default function MainLayout() {
  return (
    <div className="min-h-screen bg-[#0a0f1c] flex">
      <Sidebar />
      <div className="flex-1 flex flex-col ml-64">
        <TopBar />
        <main className="flex-1 p-8 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
