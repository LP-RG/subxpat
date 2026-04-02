module abs_diff_i336_o168(a,b,r);
input [167:0] a,b;
output [167:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
