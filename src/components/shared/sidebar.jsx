import { useState } from 'react';
import DashboardNav from '../shared/dashboard-nav';
import { navItems } from '../../constants/data';
import { useSidebar } from '../../hooks/use-sidebar';
import { cn } from '../../lib/utils';
import { ChevronsLeft } from 'lucide-react';
import logo from '../../images/whitelogo.png';

export default function Sidebar({ className }) {
  const { isMinimized, toggle } = useSidebar();
  const [status, setStatus] = useState(false);

  const handleToggle = () => {
    setStatus(true);
    toggle();
    setTimeout(() => setStatus(false), 500);
  };
  return (
    <nav
      className={cn(
        `relative z-10 hidden h-screen flex-none bg-blue-800 px-3 md:block`,
        status && 'duration-500',
        !isMinimized ? 'w-56' : 'w-[80px]',
        className
      )}
    >
      <div
        className={cn(
          'flex items-center px-0 py-5 md:px-2',
          isMinimized ? 'justify-center' : 'justify-between'
        )}
      >
        {!isMinimized && (
          <div className="mb-8 flex justify-center">
            <img src={logo} alt="Petrox logo" className="h-24 object-contain" />
          </div>
        )}
        <ChevronsLeft
          className={cn(
            'bg-background text-foreground size-8 cursor-pointer rounded-full border text-white',
            isMinimized && 'rotate-180'
          )}
          onClick={handleToggle}
        />
      </div>
      <div className="space-y-4 py-4">
        <div className="px-2 py-2">
          <div className="mt-3 space-y-1">
            <DashboardNav items={navItems} />
          </div>
        </div>
      </div>
    </nav>
  );
}
