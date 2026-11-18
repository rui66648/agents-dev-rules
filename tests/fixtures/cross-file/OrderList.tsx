import { PageHeader, FilterBar, DataTable, Pagination } from "@/components";

interface Props {
  orders: unknown[];
}

export default function OrderList({ orders }: Props) {
  return (
    <div>
      <PageHeader title="订单列表" />
      <FilterBar />
      <DataTable data={orders} />
      <Pagination total={orders.length} />
    </div>
  );
}
