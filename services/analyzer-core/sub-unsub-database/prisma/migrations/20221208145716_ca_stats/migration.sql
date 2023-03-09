-- CreateTable
CREATE TABLE "CAStats" (
    "id" SERIAL NOT NULL,
    "userId" VARCHAR(32) NOT NULL,
    "channelId" VARCHAR(32) NOT NULL,
    "gender" VARCHAR(10),
    "age" DECIMAL(3,0),

    CONSTRAINT "CAStats_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "CAStats_gender_idx" ON "CAStats"("gender");

-- CreateIndex
CREATE INDEX "CAStats_age_idx" ON "CAStats"("age");

-- CreateIndex
CREATE UNIQUE INDEX "CAStats_userId_channelId_key" ON "CAStats"("userId", "channelId");
