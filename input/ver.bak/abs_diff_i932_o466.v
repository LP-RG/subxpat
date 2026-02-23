module abs_diff_i932_o466(a,b,r);
input [465:0] a,b;
output [465:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
