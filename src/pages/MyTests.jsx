// src/components/History.jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Breadcrumbs from '../components/shared/breadcrumbs';
import Modal from '../components/ui/modal';
import { Button } from '../components/ui/button';
import CreateTest from '../components/shared/create-test';
import { useGetTests } from '@/hooks/tests';
import { DataTableSkeleton } from '@/components/shared/data-table-skeleton';
import DataTable from '@/components/shared/data-table';
import dayjs from 'dayjs';

// import { Checkbox } from '@/components/ui/checkbox';
// import { Admin } from '@/constants/data';
// import { c } from '@tanstack/react-table';
// import { CellAction } from './cell-action';

export const columns = [
  {
    id: 'course',
    header: 'Course',
    cell: ({ row }) => <p>{row?.original?.course}</p>
  },
  {
    id: 'score',
    header: 'Score',
    cell: ({ row }) => {
      const scorePercentage =
        (row?.original?.score * 100) / row?.original?.questions?.length;
      return (
        <span
          className={`rounded-full px-2 py-1 text-xs font-semibold ${
            scorePercentage >= 80
              ? 'bg-green-100 text-green-800'
              : scorePercentage >= 60
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-red-100 text-red-800'
          }`}
        >
          {row?.original?.score ? `${scorePercentage}%` : 'n/a'}
        </span>
      );
    }
  },
  {
    id: 'questions',
    header: 'No Of Questions',
    cell: ({ row }) => <>{row?.original?.questions?.length || 'n/a'}</>
  },
  // {
  //   accessorKey: 'lga',
  //   header: 'LGA'
  // },
  // {
  //   accessorKey: 'ward',
  //   header: 'WARD'
  // },
  // {
  //   accessorKey: 'address',
  //   header: 'ADDRESS'
  // },
  // {
  //   id: 'actions',
  //   cell: ({ row }) => <>{new Date(row.start_time).toLocaleString()}</>
  // }
  {
    id: 'start_time',
    header: 'Scheduled Time',
    cell: ({ row }) => (
      <p>{dayjs(row?.original?.start_time).format('DD/MM/YYYY')}</p>
    )
  }
];

function CreateTestModal({ title, isOpen, description, onClose }) {
  // This component can be used to create a new test session
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      className={'mx-auto w-full max-w-2xl rounded-lg bg-white p-6'}
    >
      <div>
        <CreateTest />
        <div className="flex w-full items-center justify-end space-x-2 pt-6">
          {/* <Button disabled={loading} variant="outline" onClick={onClose}>
          Cancel
        </Button>
        <Button disabled={loading} variant="destructive" onClick={onConfirm}>
          Continue
        </Button> */}
        </div>
      </div>
    </Modal>
  );
}

export default function MyTests() {
  const page = 1;
  const pageLimit = 10;
  // const [records, setRecords] = useState([]);
  // const [loading, setLoading] = useState(true);
  const [isOpen, setIsOpen] = useState(false);
  const navigate = useNavigate();

  const { loading, data } = useGetTests();

  const records = data?.data ?? [];

  const total = records.length;

  const pageCount = Math.ceil((total ?? 0) / pageLimit);

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="mx-auto h-[100vh] overflow-y-auto rounded-xl bg-white p-6 shadow">
        <Breadcrumbs
          items={[
            { title: 'Dashboard', link: '/dashboard' },
            { title: 'My Test', link: '/history' }
          ]}
          className="mb-4"
        />
        <div className="mb-4 flex justify-end">
          <Button onClick={() => setIsOpen(true)} className="mb-4 text-black">
            Create New Test
          </Button>
        </div>
        {loading ? (
          <DataTableSkeleton
            columnCount={10}
            filterableColumnCount={2}
            searchableColumnCount={1}
          />
        ) : records.length === 0 ? (
          <p className="mt-4 text-2xl text-gray-600">
            You haven't taken any tests yet.
          </p>
        ) : (
          <div className="space-y-4">
            <DataTable columns={columns} data={records} pageCount={pageCount} />
          </div>
        )}
      </div>
      <CreateTestModal
        loading={loading}
        title="Create Test"
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        description="Create test by filling the form fields"
      />
    </div>
  );
}
