module abs_diff_i836_o418(a,b,r);
input [417:0] a,b;
output [417:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
