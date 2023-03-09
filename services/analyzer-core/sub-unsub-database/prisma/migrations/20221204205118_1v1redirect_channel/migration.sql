/*
  Warnings:

  - A unique constraint covering the columns `[channelKey]` on the table `SupportRedirect` will be added. If there are existing duplicate values, this will fail.

*/
-- DropIndex
DROP INDEX "SupportRedirect_channelKey_idx";

-- CreateIndex
CREATE UNIQUE INDEX "SupportRedirect_channelKey_key" ON "SupportRedirect"("channelKey");
