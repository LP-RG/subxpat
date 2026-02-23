module abs_diff_i76_o38(a,b,r);
input [37:0] a,b;
output [37:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
