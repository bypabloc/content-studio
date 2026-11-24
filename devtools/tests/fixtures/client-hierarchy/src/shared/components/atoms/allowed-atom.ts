import { cn } from 'cn';
import { Button } from '../shadcn/button';
import { UIIcon } from './UIIcon';
import { type LucideIcon } from 'lucide-react';

export const parts = [cn, Button, UIIcon] as const;
export type Icon = LucideIcon;
