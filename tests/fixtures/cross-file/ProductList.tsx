import { PageHeader, DataTable, Pagination, Modal } from "@/components";

interface Props {
  products: unknown[];
}

export default function ProductList({ products }: Props) {
  return (
    <div>
      <PageHeader title="商品管理" />
      {/* 漂移：缺 FilterBar，且用 Modal 删除（列表页禁止 Modal） */}
      <Modal visible={false}>
        <button onClick={() => {}}>删除</button>
      </Modal>
      <DataTable data={products} />
      <Pagination total={products.length} />
    </div>
  );
}
