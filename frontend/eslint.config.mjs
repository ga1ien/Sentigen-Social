import { dirname } from "path";
import { fileURLToPath } from "url";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const eslintConfig = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    rules: {
      // Enforce snake_case for API-related interfaces and types
      "@typescript-eslint/naming-convention": [
        "error",
        // Interface properties should be snake_case when they represent API data
        {
          selector: "property",
          filter: {
            regex: "^(id|created_at|updated_at|user_id|workspace_id|avatar_id|voice_id|script_id|video_id|media_url|schedule_date|random_post|platform_post_id|error_message|additional_info|ref_id|post_content|platform_results|scheduled_for|heygen_video_id|thumbnail_url|aspect_ratio|video_url|preview_url|avatar_type|display_order|is_default|is_public|target_audience|video_style|duration_target|quality_score|subscription_tier|monthly_limit|videos_this_month|credits_reset_at|premium_until|last_used_at|connected_at|token_expires_at|account_metadata|is_active|full_name|avatar_url|onboarding_completed|is_admin|notification_settings|ai_preferences|dashboard_layout|platform_id|account_name|account_id|access_token|refresh_token|original_filename|media_type|file_size|mime_type|ai_generated|ai_provider|ai_model|ai_prompt|workflow_id|source_url|sentiment_score|trending_topics|comments_summary|extracted_at|engagement_score|post_id|platform_results|ayrshare_post_id|analytics|ai_generated|platform_analytics|metric_name|metric_value|metric_type|recorded_at|collected_at|engagement_rate|raw_data|impressions|reach|likes|comments|shares|clicks|saves|content_type|scheduled_for|published_at|metadata|tags|hashtags|mentions|platforms|media_assets|content_insights|workflow_executions|worker_tasks|worker_results|script_generations|video_generations|avatar_profiles|avatar_usage_stats|user_video_limits|social_platforms|user_social_accounts|content_posts|content_media|content_templates|content_recommendations|media_assets|platform_analytics|post_analytics|post_publications|scan_history|user_activity_logs|user_preferences|campaigns|workspace_members|workspaces)$",
            match: true
          },
          format: ["snake_case"]
        },
        // Variables and functions should be camelCase (standard JS/TS)
        {
          selector: "variableLike",
          format: ["camelCase", "PascalCase", "UPPER_CASE"],
          filter: {
            regex: "^(__|React|Component|Props|State|Ref|Element|Event|Handler|Provider|Context|Hook|Query|Mutation|Router|Navigation|Theme|Toast|Dialog|Modal|Form|Input|Button|Card|Table|List|Grid|Layout|Sidebar|Header|Footer|Content|Main|Section|Article|Aside|Nav|Menu|Item|Link|Image|Icon|Avatar|Badge|Label|Title|Subtitle|Description|Text|Paragraph|Heading|Caption|Code|Pre|Blockquote|List|ListItem|OrderedList|UnorderedList|Table|TableRow|TableCell|TableHeader|TableBody|TableFooter|Form|FormField|FormItem|FormLabel|FormControl|FormDescription|FormMessage|Input|Textarea|Select|SelectContent|SelectItem|SelectTrigger|SelectValue|Checkbox|RadioGroup|RadioGroupItem|Switch|Slider|Progress|Separator|Skeleton|Spinner|Loading|Error|Success|Warning|Info|Alert|AlertDialog|AlertDialogAction|AlertDialogCancel|AlertDialogContent|AlertDialogDescription|AlertDialogFooter|AlertDialogHeader|AlertDialogTitle|AlertDialogTrigger|Dialog|DialogContent|DialogDescription|DialogFooter|DialogHeader|DialogTitle|DialogTrigger|Popover|PopoverContent|PopoverTrigger|Tooltip|TooltipContent|TooltipProvider|TooltipTrigger|DropdownMenu|DropdownMenuContent|DropdownMenuItem|DropdownMenuLabel|DropdownMenuSeparator|DropdownMenuTrigger|NavigationMenu|NavigationMenuContent|NavigationMenuItem|NavigationMenuLink|NavigationMenuList|NavigationMenuTrigger|Sheet|SheetContent|SheetDescription|SheetFooter|SheetHeader|SheetTitle|SheetTrigger|Tabs|TabsContent|TabsList|TabsTrigger|Calendar|Command|CommandDialog|CommandEmpty|CommandGroup|CommandInput|CommandItem|CommandList|CommandSeparator|CommandShortcut)$",
            match: false
          }
        },
        // Functions should be camelCase
        {
          selector: "function",
          format: ["camelCase", "PascalCase"]
        },
        // Types and interfaces should be PascalCase
        {
          selector: "typeLike",
          format: ["PascalCase"]
        }
      ]
    }
  }
];

export default eslintConfig;
