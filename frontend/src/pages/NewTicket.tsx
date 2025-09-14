import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { 
  ArrowLeft, 
  Save, 
  Bot, 
  Upload, 
  X,
  Plus,
  AlertTriangle,
  Info,
  CheckCircle
} from "lucide-react";
import { Link } from "react-router-dom";
import { showSuccess, showError, showLoading } from "@/utils/toast";
import { TicketCreateRequest } from "@/types";

const categories = [
  "Integration", 
  "Authentication", 
  "Performance", 
  "Security", 
  "Mobile", 
  "Database",
  "API",
  "UI/UX",
  "Other"
];

const priorities = [
  { value: "low", label: "Low", color: "bg-gray-100 text-gray-800" },
  { value: "medium", label: "Medium", color: "bg-blue-100 text-blue-800" },
  { value: "high", label: "High", color: "bg-orange-100 text-orange-800" },
  { value: "urgent", label: "Urgent", color: "bg-red-100 text-red-800" }
];

export default function NewTicket() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [attachments, setAttachments] = useState<File[]>([]);

  const [ticketData, setTicketData] = useState<TicketCreateRequest>({
    title: "",
    description: "",
    category: "",
    priority: "medium",
    customer_email: "",
    metadata: {},
    auto_process: true
  });

  const [customFields, setCustomFields] = useState<Array<{ key: string; value: string }>>([]);

  const handleAddCustomField = () => {
    setCustomFields(prev => [...prev, { key: "", value: "" }]);
  };

  const handleRemoveCustomField = (index: number) => {
    setCustomFields(prev => prev.filter((_, i) => i !== index));
  };

  const handleCustomFieldChange = (index: number, field: 'key' | 'value', value: string) => {
    setCustomFields(prev => prev.map((item, i) => 
      i === index ? { ...item, [field]: value } : item
    ));
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    setAttachments(prev => [...prev, ...files]);
  };

  const handleRemoveAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!ticketData.title || !ticketData.description || !ticketData.category || !ticketData.customer_email) {
      showError("Please fill in all required fields");
      return;
    }

    try {
      setLoading(true);
      const loadingToast = showLoading("Creating ticket...");

      // Prepare metadata with custom fields
      const metadata = {
        ...ticketData.metadata,
        ...Object.fromEntries(
          customFields
            .filter(field => field.key && field.value)
            .map(field => [field.key, field.value])
        ),
        attachments: attachments.map(file => ({
          name: file.name,
          size: file.size,
          type: file.type
        }))
      };

      const finalTicketData = {
        ...ticketData,
        metadata
      };

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));

      showSuccess("Ticket created successfully!");
      
      // Navigate to tickets list or the new ticket detail
      navigate("/tickets");
      
    } catch (error) {
      showError("Failed to create ticket");
    } finally {
      setLoading(false);
    }
  };

  const getPriorityColor = (priority: string) => {
    return priorities.find(p => p.value === priority)?.color || "bg-gray-100 text-gray-800";
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link to="/tickets">
          <Button variant="outline" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Tickets
          </Button>
        </Link>
        
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Create New Ticket</h1>
          <p className="text-gray-600 mt-1">
            Submit a new support ticket for AI processing
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Form */}
          <div className="lg:col-span-2 space-y-6">
            {/* Basic Information */}
            <Card>
              <CardHeader>
                <CardTitle>Basic Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="title">Title *</Label>
                  <Input
                    id="title"
                    placeholder="Brief description of the issue"
                    value={ticketData.title}
                    onChange={(e) => setTicketData(prev => ({ ...prev, title: e.target.value }))}
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="description">Description *</Label>
                  <Textarea
                    id="description"
                    placeholder="Detailed description of the issue, including steps to reproduce, expected behavior, and any error messages..."
                    rows={6}
                    value={ticketData.description}
                    onChange={(e) => setTicketData(prev => ({ ...prev, description: e.target.value }))}
                    required
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    Provide as much detail as possible to help the AI agent understand and resolve the issue.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="category">Category *</Label>
                    <Select value={ticketData.category} onValueChange={(value) => setTicketData(prev => ({ ...prev, category: value }))}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select category" />
                      </SelectTrigger>
                      <SelectContent>
                        {categories.map(category => (
                          <SelectItem key={category} value={category}>{category}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label htmlFor="priority">Priority *</Label>
                    <Select value={ticketData.priority} onValueChange={(value: any) => setTicketData(prev => ({ ...prev, priority: value }))}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {priorities.map(priority => (
                          <SelectItem key={priority.value} value={priority.value}>
                            <div className="flex items-center gap-2">
                              <Badge className={priority.color}>{priority.label}</Badge>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div>
                  <Label htmlFor="email">Customer Email *</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="customer@company.com"
                    value={ticketData.customer_email}
                    onChange={(e) => setTicketData(prev => ({ ...prev, customer_email: e.target.value }))}
                    required
                  />
                </div>
              </CardContent>
            </Card>

            {/* Attachments */}
            <Card>
              <CardHeader>
                <CardTitle>Attachments</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="file-upload">Upload Files</Label>
                  <Input
                    id="file-upload"
                    type="file"
                    multiple
                    onChange={handleFileUpload}
                    className="cursor-pointer"
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    Upload screenshots, logs, or other relevant files (max 10MB per file)
                  </p>
                </div>

                {attachments.length > 0 && (
                  <div className="space-y-2">
                    <Label>Attached Files:</Label>
                    {attachments.map((file, index) => (
                      <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                        <div className="flex items-center gap-2">
                          <Upload className="w-4 h-4 text-gray-500" />
                          <span className="text-sm">{file.name}</span>
                          <Badge variant="outline" className="text-xs">
                            {(file.size / 1024 / 1024).toFixed(2)} MB
                          </Badge>
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRemoveAttachment(index)}
                        >
                          <X className="w-4 h-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Custom Fields */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Additional Information</CardTitle>
                  <Button type="button" variant="outline" size="sm" onClick={handleAddCustomField}>
                    <Plus className="w-4 h-4 mr-2" />
                    Add Field
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {customFields.length === 0 ? (
                  <p className="text-sm text-gray-500 text-center py-4">
                    No additional fields added. Click "Add Field" to include custom information.
                  </p>
                ) : (
                  <div className="space-y-3">
                    {customFields.map((field, index) => (
                      <div key={index} className="flex items-center gap-3">
                        <Input
                          placeholder="Field name"
                          value={field.key}
                          onChange={(e) => handleCustomFieldChange(index, 'key', e.target.value)}
                        />
                        <Input
                          placeholder="Field value"
                          value={field.value}
                          onChange={(e) => handleCustomFieldChange(index, 'value', e.target.value)}
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRemoveCustomField(index)}
                        >
                          <X className="w-4 h-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* AI Processing */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Bot className="w-5 h-5 text-blue-600" />
                  AI Processing
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Auto-process with AI</Label>
                    <p className="text-sm text-gray-600">
                      Automatically analyze and attempt to resolve this ticket
                    </p>
                  </div>
                  <Switch
                    checked={ticketData.auto_process}
                    onCheckedChange={(checked) => setTicketData(prev => ({ ...prev, auto_process: checked }))}
                  />
                </div>

                {ticketData.auto_process && (
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <div className="flex items-start gap-2">
                      <Info className="w-4 h-4 text-blue-600 mt-0.5" />
                      <div className="text-sm text-blue-800">
                        <p className="font-medium">AI Processing Enabled</p>
                        <p>The ticket will be automatically analyzed and processed by our AI agent upon creation.</p>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Ticket Preview */}
            <Card>
              <CardHeader>
                <CardTitle>Ticket Preview</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <Label className="text-xs text-gray-500">TITLE</Label>
                  <p className="text-sm font-medium">
                    {ticketData.title || "No title provided"}
                  </p>
                </div>

                <div>
                  <Label className="text-xs text-gray-500">CATEGORY</Label>
                  <p className="text-sm">
                    {ticketData.category || "No category selected"}
                  </p>
                </div>

                <div>
                  <Label className="text-xs text-gray-500">PRIORITY</Label>
                  <Badge className={getPriorityColor(ticketData.priority)}>
                    {priorities.find(p => p.value === ticketData.priority)?.label}
                  </Badge>
                </div>

                <div>
                  <Label className="text-xs text-gray-500">CUSTOMER</Label>
                  <p className="text-sm">
                    {ticketData.customer_email || "No email provided"}
                  </p>
                </div>

                {attachments.length > 0 && (
                  <div>
                    <Label className="text-xs text-gray-500">ATTACHMENTS</Label>
                    <p className="text-sm">{attachments.length} file(s)</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Submit Actions */}
            <Card>
              <CardContent className="p-4">
                <div className="space-y-3">
                  <Button type="submit" disabled={loading} className="w-full">
                    <Save className="w-4 h-4 mr-2" />
                    {loading ? "Creating..." : "Create Ticket"}
                  </Button>
                  
                  <Button type="button" variant="outline" className="w-full" asChild>
                    <Link to="/tickets">Cancel</Link>
                  </Button>
                </div>

                {ticketData.auto_process && (
                  <div className="mt-4 p-3 bg-green-50 rounded-lg">
                    <div className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-600 mt-0.5" />
                      <div className="text-sm text-green-800">
                        <p className="font-medium">Ready for AI Processing</p>
                        <p>This ticket will be automatically processed upon creation.</p>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </form>
    </div>
  );
}