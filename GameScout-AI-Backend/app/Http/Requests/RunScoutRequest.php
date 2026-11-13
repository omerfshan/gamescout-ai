<?php
declare(strict_types=1);
namespace App\Http\Requests;
use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;
final class RunScoutRequest extends FormRequest
{
    public function authorize(): bool { return $this->user() !== null; }
    public function rules(): array
    {
        return [
            'provider' => ['sometimes', 'string', Rule::in(['auto', 'ollama', 'openai', 'gemini', 'heuristic'])],
        ];
    }
}
