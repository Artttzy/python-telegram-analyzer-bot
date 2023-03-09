/*
  Warnings:

  - A unique constraint covering the columns `[externalId]` on the table `CallCenter` will be added. If there are existing duplicate values, this will fail.
  - The required column `externalId` was added to the `CallCenter` table with a prisma-level default value. This is not possible if the table is not empty. Please add this column as optional, then populate it before making it required.

*/
-- AlterTable
ALTER TABLE "CallCenter" ADD COLUMN     "externalId" UUID NOT NULL;

-- CreateIndex
CREATE UNIQUE INDEX "CallCenter_externalId_key" ON "CallCenter"("externalId");
