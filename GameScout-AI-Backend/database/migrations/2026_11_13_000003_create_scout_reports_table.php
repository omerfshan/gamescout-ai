<?php
declare(strict_types=1);
use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;
return new class extends Migration {
    public function up(): void
    {
        Schema::create('scout_reports', function (Blueprint $table): void {
            $table->id();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->string('scan_id', 128);
            $table->string('ai_engine_used', 128);
            $table->jsonb('report_payload');
            $table->timestamp('scanned_at');
            $table->timestamps();
            $table->index(['user_id', 'id']);
        });
    }
    public function down(): void
    {
        Schema::dropIfExists('scout_reports');
    }
};
