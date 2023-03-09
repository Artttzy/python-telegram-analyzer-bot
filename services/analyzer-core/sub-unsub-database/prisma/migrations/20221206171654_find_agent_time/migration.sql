/*
  Warnings:

  - Added the required column `findTime` to the `SupportTicket` table without a default value. This is not possible if the table is not empty.

*/
-- AlterTable
ALTER TABLE "SupportTicket" ADD COLUMN     "findTime" TIMESTAMPTZ(3) NOT NULL;
