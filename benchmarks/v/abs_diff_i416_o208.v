module abs_diff_i416_o208(a,b,r);
input [207:0] a,b;
output [207:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
