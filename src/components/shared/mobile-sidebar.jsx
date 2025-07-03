import DashboardNav from './dashboard-nav';
import { Sheet, SheetContent } from '../ui/sheet';
import { navItems } from '../../constants/data';
import { Link } from 'react-router-dom';
import logo from '../../images/whitelogo.png';

export default function MobileSidebar({ setSidebarOpen, sidebarOpen }) {
  return (
    <>
      <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
        <SheetContent side="left" className="bg-background !px-0">
          <div className="space-y-4 py-4">
            <div className="space-y-4 px-3 py-2">
              <Link to="/" className="px-2 py-2 text-2xl font-bold text-white">
                  <img src={logo} alt="Petrox logo" className="h-24 object-contain" />
              </Link>
              <div className="space-y-1 px-2">
                <DashboardNav items={navItems} setOpen={setSidebarOpen} />
              </div>
            </div>
          </div>
        </SheetContent>
      </Sheet>
    </>
  );
}
