import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import {
  Search,
  Plus,
  Upload,
  Globe,
  FileText,
  Tag,
  Eye,
  Edit,
  Trash2,
  Download,
  Filter,
  BookOpen,
  ExternalLink,
} from "lucide-react";
import { KBArticle } from "@/types";
import { showSuccess, showError } from "@/utils/toast";
import { formatDistanceToNow } from "date-fns";
import { useKBArticles } from "@/hooks";
import { api } from "@/services/api";

// Mock KB articles data
const mockKBArticles: KBArticle[] = [
  {
    id: 1,
    title: "Troubleshooting SMTP Configuration Issues",
    content:
      "This comprehensive guide covers common SMTP configuration problems and their solutions. SMTP (Simple Mail Transfer Protocol) is crucial for email delivery...",
    category: "Email",
    tags: ["smtp", "email", "configuration", "troubleshooting"],
    relevance_score: 0.95,
    content_preview:
      "Step-by-step guide to diagnose and fix SMTP timeout issues, including configuration examples and common pitfalls.",
  },
  {
    id: 2,
    title: "Email Service Restart Procedures",
    content:
      "Safe procedures for restarting email services without losing queued messages. This guide ensures minimal downtime...",
    category: "Operations",
    tags: ["email", "restart", "maintenance", "procedures"],
    relevance_score: 0.78,
    content_preview:
      "Safe procedures for restarting email services without losing queued messages.",
  },
  {
    id: 3,
    title: "Database Performance Optimization",
    content:
      "Comprehensive guide to optimizing database performance including indexing strategies, query optimization...",
    category: "Performance",
    tags: ["database", "performance", "optimization", "indexing"],
    relevance_score: 0.89,
    content_preview:
      "Learn how to optimize database queries and improve overall system performance.",
  },
  {
    id: 4,
    title: "Security Best Practices for Web Applications",
    content:
      "Essential security practices for web applications including authentication, authorization, data validation...",
    category: "Security",
    tags: ["security", "web", "authentication", "best-practices"],
    relevance_score: 0.92,
    content_preview:
      "Comprehensive security guidelines to protect your web applications from common vulnerabilities.",
  },
  {
    id: 5,
    title: "Mobile App Crash Debugging Guide",
    content:
      "Step-by-step guide to debug mobile application crashes, including log analysis and common crash patterns...",
    category: "Mobile",
    tags: ["mobile", "debugging", "crashes", "ios", "android"],
    relevance_score: 0.85,
    content_preview:
      "Learn how to effectively debug and resolve mobile application crashes.",
  },
];

const categories = [
  "All",
  "Email",
  "Operations",
  "Performance",
  "Security",
  "Mobile",
  "Integration",
];

export default function KnowledgeBase() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isUploadDialogOpen, setIsUploadDialogOpen] = useState(false);
  const [isCrawlDialogOpen, setIsCrawlDialogOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const { data: apiArticles, error, isLoading } = useKBArticles();
  const articles = apiArticles || mockKBArticles;
  // New article form state
  const [newArticle, setNewArticle] = useState({
    title: "",
    content: "",
    category: "",
    tags: "",
  });

  // Upload form state
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadCategory, setUploadCategory] = useState("");

  // URL crawl form state
  const [crawlUrl, setCrawlUrl] = useState("");
  const [crawlCategory, setCrawlCategory] = useState("");
  const [maxDepth, setMaxDepth] = useState(1);

  // Get all unique tags
  const allTags = Array.from(
    new Set(articles.flatMap((article) => article.tags))
  );

  // Filter articles
  const filteredArticles = articles.filter((article) => {
    const matchesSearch =
      !searchQuery ||
      article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      article.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
      article.tags.some((tag) =>
        tag.toLowerCase().includes(searchQuery.toLowerCase())
      );

    const matchesCategory =
      selectedCategory === "All" || article.category === selectedCategory;
    const matchesTags =
      selectedTags.length === 0 ||
      selectedTags.some((tag) => article.tags.includes(tag));

    return matchesSearch && matchesCategory && matchesTags;
  });

  const handleCreateArticle = async () => {
    if (!newArticle.title || !newArticle.content || !newArticle.category) {
      showError("Please fill in all required fields");
      return;
    }

    try {
      setLoading(true);
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1000));

      const article: KBArticle = {
        id: articles.length + 1,
        title: newArticle.title,
        content: newArticle.content,
        category: newArticle.category,
        tags: newArticle.tags
          .split(",")
          .map((tag) => tag.trim())
          .filter(Boolean),
        content_preview: newArticle.content.substring(0, 150) + "...",
      };

      // setArticles((prev) => [article, ...prev]);
      setNewArticle({ title: "", content: "", category: "", tags: "" });
      setIsCreateDialogOpen(false);
      showSuccess("Article created successfully");
    } catch (error) {
      showError("Failed to create article");
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async () => {
    if (!uploadFile || !uploadCategory) {
      showError("Please select a file and category");
      return;
    }

    try {
      setLoading(true);
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 2000));

      showSuccess(
        `File "${uploadFile.name}" uploaded and processed successfully`
      );
      setUploadFile(null);
      setUploadCategory("");
      setIsUploadDialogOpen(false);
    } catch (error) {
      showError("Failed to upload file");
    } finally {
      setLoading(false);
    }
  };

  const handleUrlCrawl = async () => {
    if (!crawlUrl || !crawlCategory) {
      showError("Please enter a URL and select a category");
      return;
    }

    try {
      setLoading(true);
      // Simulate API call
      await api.crawlURL(crawlUrl, crawlCategory, maxDepth);

      showSuccess(`URL crawled successfully..`);
      setCrawlUrl("");
      setCrawlCategory("");
      setMaxDepth(1);
      setIsCrawlDialogOpen(false);
    } catch (error) {
      console.log(error);

      showError("Failed to crawl URL");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteArticle = async (id: number) => {
    try {
      setLoading(true);
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 500));

      setArticles((prev) => prev.filter((article) => article.id !== id));
      showSuccess("Article deleted successfully");
    } catch (error) {
      showError("Failed to delete article");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Knowledge Base</h1>
          <p className="text-gray-600 mt-1">
            Manage articles and documentation for AI agent training
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Dialog open={isCrawlDialogOpen} onOpenChange={setIsCrawlDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" className="flex items-center gap-2">
                <Globe className="w-4 h-4" />
                Crawl URL
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Crawl Website for Knowledge</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="crawl-url">Website URL</Label>
                  <Input
                    id="crawl-url"
                    placeholder="https://example.com/docs"
                    value={crawlUrl}
                    onChange={(e) => setCrawlUrl(e.target.value)}
                  />
                </div>
                <div>
                  <Label htmlFor="crawl-category">Category</Label>
                  <Select
                    value={crawlCategory}
                    onValueChange={setCrawlCategory}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select category" />
                    </SelectTrigger>
                    <SelectContent>
                      {categories
                        .filter((cat) => cat !== "All")
                        .map((category) => (
                          <SelectItem key={category} value={category}>
                            {category}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="max-depth">Max Crawl Depth</Label>
                  <Select
                    value={maxDepth.toString()}
                    onValueChange={(value) => setMaxDepth(parseInt(value))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">1 level</SelectItem>
                      <SelectItem value="2">2 levels</SelectItem>
                      <SelectItem value="3">3 levels</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button
                  onClick={handleUrlCrawl}
                  disabled={loading}
                  className="w-full"
                >
                  {loading ? "Crawling..." : "Start Crawling"}
                </Button>
              </div>
            </DialogContent>
          </Dialog>

          <Dialog
            open={isUploadDialogOpen}
            onOpenChange={setIsUploadDialogOpen}
          >
            <DialogTrigger asChild>
              <Button variant="outline" className="flex items-center gap-2">
                <Upload className="w-4 h-4" />
                Upload File
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Upload Knowledge File</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="file-upload">Select File</Label>
                  <Input
                    id="file-upload"
                    type="file"
                    accept=".pdf,.doc,.docx,.txt,.md"
                    onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Supported formats: PDF, DOC, DOCX, TXT, MD
                  </p>
                </div>
                <div>
                  <Label htmlFor="upload-category">Category</Label>
                  <Select
                    value={uploadCategory}
                    onValueChange={setUploadCategory}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select category" />
                    </SelectTrigger>
                    <SelectContent>
                      {categories
                        .filter((cat) => cat !== "All")
                        .map((category) => (
                          <SelectItem key={category} value={category}>
                            {category}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                </div>
                <Button
                  onClick={handleFileUpload}
                  disabled={loading || !uploadFile}
                  className="w-full"
                >
                  {loading ? "Uploading..." : "Upload & Process"}
                </Button>
              </div>
            </DialogContent>
          </Dialog>

          <Dialog
            open={isCreateDialogOpen}
            onOpenChange={setIsCreateDialogOpen}
          >
            <DialogTrigger asChild>
              <Button className="flex items-center gap-2">
                <Plus className="w-4 h-4" />
                New Article
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Create New Article</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="title">Title</Label>
                  <Input
                    id="title"
                    placeholder="Article title"
                    value={newArticle.title}
                    onChange={(e) =>
                      setNewArticle((prev) => ({
                        ...prev,
                        title: e.target.value,
                      }))
                    }
                  />
                </div>
                <div>
                  <Label htmlFor="category">Category</Label>
                  <Select
                    value={newArticle.category}
                    onValueChange={(value) =>
                      setNewArticle((prev) => ({ ...prev, category: value }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select category" />
                    </SelectTrigger>
                    <SelectContent>
                      {categories
                        .filter((cat) => cat !== "All")
                        .map((category) => (
                          <SelectItem key={category} value={category}>
                            {category}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="tags">Tags (comma-separated)</Label>
                  <Input
                    id="tags"
                    placeholder="tag1, tag2, tag3"
                    value={newArticle.tags}
                    onChange={(e) =>
                      setNewArticle((prev) => ({
                        ...prev,
                        tags: e.target.value,
                      }))
                    }
                  />
                </div>
                <div>
                  <Label htmlFor="content">Content</Label>
                  <Textarea
                    id="content"
                    placeholder="Article content..."
                    rows={10}
                    value={newArticle.content}
                    onChange={(e) =>
                      setNewArticle((prev) => ({
                        ...prev,
                        content: e.target.value,
                      }))
                    }
                  />
                </div>
                <Button
                  onClick={handleCreateArticle}
                  disabled={loading}
                  className="w-full"
                >
                  {loading ? "Creating..." : "Create Article"}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col lg:flex-row gap-4">
            {/* Search */}
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="Search articles by title, content, or tags..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            {/* Category Filter */}
            <Select
              value={selectedCategory}
              onValueChange={setSelectedCategory}
            >
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {categories.map((category) => (
                  <SelectItem key={category} value={category}>
                    {category}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Button variant="outline" size="icon">
              <Filter className="w-4 h-4" />
            </Button>
          </div>

          {/* Tag Filters */}
          {allTags.length > 0 && (
            <div className="mt-4">
              <Label className="text-sm font-medium mb-2 block">
                Filter by Tags:
              </Label>
              <div className="flex flex-wrap gap-2">
                {allTags.slice(0, 10).map((tag) => (
                  <Badge
                    key={tag}
                    variant={selectedTags.includes(tag) ? "default" : "outline"}
                    className="cursor-pointer"
                    onClick={() => {
                      setSelectedTags((prev) =>
                        prev.includes(tag)
                          ? prev.filter((t) => t !== tag)
                          : [...prev, tag]
                      );
                    }}
                  >
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Articles Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {filteredArticles.map((article) => (
          <Card key={article.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle className="text-lg line-clamp-2">
                    {article.title}
                  </CardTitle>
                  <div className="flex items-center gap-2 mt-2">
                    <Badge variant="outline">{article.category}</Badge>
                    {article.relevance_score && (
                      <Badge variant="secondary" className="text-xs">
                        {(article.relevance_score * 100).toFixed(0)}% relevant
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600 mb-4 line-clamp-3">
                {article.content_preview ||
                  article.content.substring(0, 150) + "..."}
              </p>

              <div className="flex flex-wrap gap-1 mb-4">
                {article.tags.slice(0, 3).map((tag) => (
                  <Badge key={tag} variant="secondary" className="text-xs">
                    <Tag className="w-3 h-3 mr-1" />
                    {tag}
                  </Badge>
                ))}
                {article.tags.length > 3 && (
                  <Badge variant="secondary" className="text-xs">
                    +{article.tags.length - 3} more
                  </Badge>
                )}
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="sm">
                    <Eye className="w-4 h-4 mr-1" />
                    View
                  </Button>
                  <Button variant="ghost" size="sm">
                    <Edit className="w-4 h-4 mr-1" />
                    Edit
                  </Button>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDeleteArticle(article.id)}
                  className="text-red-600 hover:text-red-700"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredArticles.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <BookOpen className="w-12 h-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No articles found
            </h3>
            <p className="text-gray-600 text-center mb-4">
              {searchQuery ||
              selectedCategory !== "All" ||
              selectedTags.length > 0
                ? "Try adjusting your search criteria or filters"
                : "Get started by creating your first knowledge base article"}
            </p>
            <Button onClick={() => setIsCreateDialogOpen(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Create First Article
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Total Articles
                </p>
                <p className="text-2xl font-bold">{articles.length}</p>
              </div>
              <FileText className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Categories</p>
                <p className="text-2xl font-bold">{categories.length - 1}</p>
              </div>
              <Tag className="w-8 h-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Unique Tags</p>
                <p className="text-2xl font-bold">{allTags.length}</p>
              </div>
              <Tag className="w-8 h-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Avg Relevance
                </p>
                <p className="text-2xl font-bold">
                  {Math.round(
                    (articles.reduce(
                      (acc, article) => acc + (article.relevance_score || 0),
                      0
                    ) /
                      articles.length) *
                      100
                  )}
                  %
                </p>
              </div>
              <BookOpen className="w-8 h-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
