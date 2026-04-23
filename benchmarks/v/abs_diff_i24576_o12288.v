module abs_diff_i24576_o12288(a,b,r);
input [12287:0] a,b;
output [12287:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
