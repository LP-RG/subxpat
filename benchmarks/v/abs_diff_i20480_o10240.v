module abs_diff_i20480_o10240(a,b,r);
input [10239:0] a,b;
output [10239:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
