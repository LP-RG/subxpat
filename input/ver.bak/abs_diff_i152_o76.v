module abs_diff_i152_o76(a,b,r);
input [75:0] a,b;
output [75:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
