import { PageHeader, FilterBar, DataTable, Pagination } from "@/components";

interface Props {
  users: unknown[];
}

export default function UserList({ users }: Props) {
  return (
    <div>
      <PageHeader title="用户管理" />
      <FilterBar />
      <DataTable data={users} />
      <Pagination total={users.length} />
    </div>
  );
}
