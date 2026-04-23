module abs_diff_i26624_o13312(a,b,r);
input [13311:0] a,b;
output [13311:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
