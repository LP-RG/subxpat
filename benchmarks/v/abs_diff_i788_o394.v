module abs_diff_i788_o394(a,b,r);
input [393:0] a,b;
output [393:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
