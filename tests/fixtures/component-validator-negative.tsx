import { Button, Modal, Drawer, Card } from "@/components/ui";

export function BadComponent() {
  return (
    <Card>
      <Card>
        <Modal>
          <Drawer>
            <Button variant="primary">确认</Button>
            <Button variant="primary">再次确认</Button>
          </Drawer>
        </Modal>
      </Card>
    </Card>
  );
}
