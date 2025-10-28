import { useState, useEffect } from "react";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Card } from "@/components/ui/card";
import { Question } from "@/data/assessmentData";
import { GripVertical } from "lucide-react";

interface SortableItemProps {
  id: string;
  content: string;
  index: number;
}

const SortableItem = ({ id, content, index }: SortableItemProps) => {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <Card className="p-4 cursor-move hover:shadow-md transition-shadow mb-2">
        <div className="flex items-center gap-3">
          <GripVertical size={20} className="text-muted-foreground" />
          <div className="flex items-center gap-3 flex-1">
            <span className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center text-sm font-semibold text-primary">
              {index + 1}
            </span>
            <span>{content}</span>
          </div>
        </div>
      </Card>
    </div>
  );
};

interface DragDropRankingProps {
  question: Question;
  answer: any;
  onAnswer: (answer: any) => void;
  language: "en" | "ar";
}

const DragDropRanking = ({ question, answer, onAnswer, language }: DragDropRankingProps) => {
  const items = language === "en" ? question.items : (question.itemsAr || question.items);
  const [sortedItems, setSortedItems] = useState(answer || items || []);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  useEffect(() => {
    if (answer) {
      setSortedItems(answer);
    }
  }, [answer]);

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      setSortedItems((items: string[]) => {
        const oldIndex = items.indexOf(active.id as string);
        const newIndex = items.indexOf(over.id as string);
        const newItems = arrayMove(items, oldIndex, newIndex);
        onAnswer(newItems);
        return newItems;
      });
    }
  };

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground mb-4">
        {language === "en"
          ? "Drag and drop the items to arrange them in the correct order"
          : "اسحب وأسقط العناصر لترتيبها بالترتيب الصحيح"}
      </p>

      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext items={sortedItems} strategy={verticalListSortingStrategy}>
          {sortedItems.map((item: string, index: number) => (
            <SortableItem key={item} id={item} content={item} index={index} />
          ))}
        </SortableContext>
      </DndContext>
    </div>
  );
};

export default DragDropRanking;
