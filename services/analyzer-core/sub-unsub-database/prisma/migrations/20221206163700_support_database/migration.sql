-- CreateTable
CREATE TABLE "CallCenter" (
    "id" SERIAL NOT NULL,
    "userId" VARCHAR(32) NOT NULL,
    "channelKey" INTEGER NOT NULL,

    CONSTRAINT "CallCenter_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "SupportAgent" (
    "id" SERIAL NOT NULL,
    "userId" VARCHAR(32) NOT NULL,
    "callCenterKey" INTEGER NOT NULL,

    CONSTRAINT "SupportAgent_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "SupportTicket" (
    "id" SERIAL NOT NULL,
    "userId" VARCHAR(32) NOT NULL,
    "agentKey" INTEGER,
    "openTime" TIMESTAMPTZ(3) NOT NULL,
    "answerTime" TIMESTAMPTZ(3),
    "closeTime" TIMESTAMPTZ(3),
    "status" VARCHAR(10) NOT NULL,

    CONSTRAINT "SupportTicket_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "CallCenter_userId_key" ON "CallCenter"("userId");

-- CreateIndex
CREATE UNIQUE INDEX "SupportAgent_userId_key" ON "SupportAgent"("userId");

-- CreateIndex
CREATE INDEX "SupportTicket_userId_idx" ON "SupportTicket"("userId");

-- CreateIndex
CREATE INDEX "SupportTicket_agentKey_idx" ON "SupportTicket"("agentKey");

-- AddForeignKey
ALTER TABLE "CallCenter" ADD CONSTRAINT "CallCenter_channelKey_fkey" FOREIGN KEY ("channelKey") REFERENCES "AdminChannel"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "SupportAgent" ADD CONSTRAINT "SupportAgent_callCenterKey_fkey" FOREIGN KEY ("callCenterKey") REFERENCES "CallCenter"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "SupportTicket" ADD CONSTRAINT "SupportTicket_agentKey_fkey" FOREIGN KEY ("agentKey") REFERENCES "SupportAgent"("id") ON DELETE SET NULL ON UPDATE CASCADE;
